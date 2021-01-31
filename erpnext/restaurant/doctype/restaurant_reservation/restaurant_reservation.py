# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# Frappe
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours, add_to_date, get_datetime, cint
# ERPNext
from erpnext.restaurant.queries import tables_query, reservations_query


class RestaurantReservation(Document):
	def validate(self):
		self.__validate_reservation()
		
	def __validate_reservation(self):
		if self.end_time is not None and not 0.5 <= time_diff_in_hours(self.end_time, self.start_time) < 12:
			frappe.throw(_("Reservations must have a duration of stay between 30 minutes and 12 hours."))
		if self.status in ['Open', 'Waitlisted', 'Rejected'] and len(self.assigned_tables) > 0:
			frappe.throw(_("Waitlisted or rejected reservations can't have assigned tables."))

	def before_save(self):
		if not self.end_time:
			restaurant = frappe.get_doc('Restaurant', self.restaurant)
			self.end_time = add_to_date(self.start_time, seconds=restaurant.default_duration_of_stay)

	@frappe.whitelist()
	def assign_table(self, save=False):
		"""Assign a single reservation to the best fitting table.

		:param reservation: The reservation which should be assigned
		"""
		# Allocate reservations to tables
		reservations, waiting_list = assign_tables2(self.restaurant, self.start_time, self.end_time)
		reservation = next((x for x in reservations if x.name == self.name), None)
		if reservation:
			if save:
				self.append("assigned_tables", {"restaurant_table": reservation.restaurant_table})
				self.save(ignore_version=True)
				self.add_comment('Label', _("assigned table {} through auto-assignment").format(frappe.bold(reservation.restaurant_table)))
				
			frappe.msgprint(
				msg=_("Reservation assigned to {0}.").format(reservation.restaurant_table),
				title='Reservation assigned',
				indicator='green'
			)
		else:
			frappe.msgprint(
				msg=_("The reservation could not be assigned to any table."),
				title=_('Not assigned'),
				indicator='red'
			)
	
	@frappe.whitelist()
	def assign_table2(self, save=False):
		"""Assign a single reservation to the best fitting table.

		:param reservation: The reservation which should be assigned
		"""
		# Allocate reservations to tables
		reservations, waiting_list = assign_tables2(self.restaurant, self.start_time, self.end_time)
		reservation = next((x for x in reservations if x.name == self.name), None)
		if reservation:
			if save:
				self.append("assigned_tables", {"restaurant_table": reservation.restaurant_table})
				self.save(ignore_version=True)
				self.add_comment('Label', _("assigned table {} through auto-assignment").format(frappe.bold(reservation.restaurant_table)))
				
			return _("Reservation assigned to {0}.").format(reservation.restaurant_table)
		else:
			return _("The reservation could not be assigned to any table.")


@frappe.whitelist()
def assign_tables(restaurant, start_time, end_time, save=False):
	"""Assign all reservations in a given time frame to the best fitting tables.

	:param restaurant: The specific restaurant
	:param start_time: The start of the time frame where reservations should be assigned
	:param end_time: The end of the time frame where reservations should be assigned
	:param save: Whether the allocations should be saved or not
	"""
	# Allocate reservations to tables
	reservations, waiting_list = assign_tables2(restaurant, start_time, end_time)
	
	reservations = sorted(reservations, key=lambda x: x.name) # Can be deleted
	if save == True:
		# Append assigned table child row
		for reservation in reservations:
			doc = frappe.get_doc('Restaurant Reservation', reservation.name)
			doc.status = 'Accepted'
			doc.append("assigned_tables", {"restaurant_table": reservation.restaurant_table})
			doc.save(ignore_permissions=True, ignore_version=True)
			doc.add_comment('Label', _("assigned table {} through auto-assignment").format(frappe.bold(reservation.restaurant_table)))
		# Change status for waitlisted reservations
		for reservation in waiting_list:
			doc = frappe.get_doc('Restaurant Reservation', reservation.name)
			doc.status = 'Waiting List'
			doc.save(ignore_permissions=True)

	if len(reservations) > 0:
		response = """
				<p>{message}</p>
				<table class=\"table\">
					<thead>
					<tr>
						<th>{res_caption}</th>
						<th>{tab_caption}</th>
					</tr>
					</thead>
					<tbody>{data}</tbody>
				</table>
				<p>{unassigned}</p>
			""".format(
					message=_("The reservations have been assigned to the following restaurant tables:"),
					res_caption=_("Reservation"),
					tab_caption=_("Restaurant Table"),
					data="\n".join(["<tr><td>{res}</td><td>{table}</td></tr>".format(res=s.name, table=s.restaurant_table) for s in reservations]),
					unassigned= frappe.bold(_("The following reservations could not be assigned: ")) + ", ".join(waiting_list) if len(waiting_list) > 0 else _("All reservations could be assigned.")
				)
		frappe.msgprint(
			msg=response,
			title='Reservations assigned',
			indicator='green',
			#wide=True
			#as_table=True
		)
	else:
		frappe.msgprint(
			msg=_("There were no reservations to assign."),
			title='No reservations assigned',
			indicator='red'
		)

# RENAME THIS FUNCTION
def assign_tables2(restaurant, start_time, end_time):
	# Validate
	if not frappe.has_permission("Restaurant Reservation", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if time_diff_in_hours(end_time, start_time) < 0.5:
		frappe.throw(_("The period for automatic assignment of reservations must be at least 30 minutes long."))
	#if start_time < frappe.utils.now():
	#	frappe.throw(_("The start date cannot be in the past."))

	# Make database queries
	db_tables = tables_query(restaurant=restaurant)
	db_reservations = reservations_query(restaurant=restaurant, start_time=start_time, end_time=end_time)
	db_restaurant = frappe.get_doc('Restaurant', restaurant)
	# Allocate reservations to tables
	return get_table_allocations(db_restaurant, db_tables, db_reservations)
	

@frappe.whitelist()
def check_availability(restaurant, no_of_people, start_time, end_time=None):
	# Query restaurant doc first
	db_restaurant = frappe.get_doc('Restaurant', restaurant)
	start_time = get_datetime(start_time)
	end_time = get_datetime(end_time) if end_time is not None else add_to_date(start_time, seconds=db_restaurant.default_duration_of_stay)

	# Validate
	if end_time is not None and time_diff_in_hours(end_time, start_time) < 0.5:
		frappe.throw(_("Restaurant reservations must be at least 30 minutes long."))
	#if start_time < frappe.utils.now():
	#	frappe.throw(_("The start date cannot be in the past."))

	# Make database queries
	db_tables = tables_query(restaurant)
	db_reservations = reservations_query(restaurant=restaurant, start_time=start_time, end_time=end_time)
	db_reservations.append(frappe._dict({
		'name': '#',
		'restaurant': restaurant,
		'no_of_people': cint(no_of_people),
		'start_time': start_time,
		'end_time': end_time,
		'assigned_tables': None,
		'creation': frappe.utils.now()
	}))
	# Allocate reservations to tables
	reservations, waiting_list = get_table_allocations(db_restaurant, db_tables, db_reservations)

	#return True if len(waiting_list) == 0 else False
	return True if not '#' in waiting_list else False

# http://localhost:8000/api/method/erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.make_restaurant_reservation?restaurant_name=Krusty%20Krab&contact_email=mw.posts%40gmail.com&no_of_people=4&start_time=2021-01-16%2018%3A00%3A00&end_time=2021-01-16%2020%3A30%3A00

@frappe.whitelist()
def make_restaurant_reservation(restaurant_name, contact_email, no_of_people, start_time, end_time=None, customer_name=None, customer_phone=None):
	"""Creates a new restaurant reservation, checks availability and sends the customer a confirmation or rejection.

	:param restaurant_name: The name of the restaurant where the reservation is made.
	"""
	restaurant = frappe.get_doc('Restaurant', restaurant_name)

	# Exit if online reservations is turned off for this restaurant
	if not restaurant.enable_online_reservations:
		return

	if end_time is None:
		end_time = add_to_date(start_time, seconds=restaurant.default_duration_of_stay)
	
	table_available = check_availability(restaurant_name, no_of_people, start_time, end_time=end_time)

	# Find customer by email or create new customer
	customer = frappe.db.get_all('Customer',
		filters={
			'email_id': contact_email
		},
		fields=['name', 'customer_name'],
		#order_by='date desc',
		#start=10,
		page_length=1
		#as_list=True
	)
	customer = customer[0] if len(customer) > 0 else None
	#if not customer:
	#	customer = frappe.get_doc({
	#		'doctype': 'Customer',
	#		'customer_name': customer_name
	#	})
	#	customer.insert()
		# customer.append("customer_primary_contact", {"restaurant_table": reservation.restaurant_table})
		# Hier weitermachen

	# Create reservation doc
	reservation = frappe.get_doc({
		'doctype': 'Restaurant Reservation',
		'docstatus': 1,
		'restaurant': restaurant.name,
		'no_of_people': no_of_people,
		'start_time': start_time,
		'end_time': end_time,
		'customer': customer.name if customer else None,
		'customer_name': 'Roland',
		'contact_phone': None,
		'contact_email': contact_email,
		'status': 'Accepted' if table_available else 'Waitlisted'
	})
	reservation.insert()

	# Send email to customer
	email_template_name = restaurant.acceptance_email_template if table_available == True else restaurant.rejection_email_template
	email_template = frappe.get_doc("Email Template", email_template_name)

	#frappe.sendmail(
	#	recipients=customer_email,
	#	subject=email_template.subject,
	#	message=frappe.render_template(email_template.response, reservation.as_dict()),
	#	#attachments=get_attachments(stop),
	#	reference_doctype=reservation.doctype,
	#	reference_name=reservation.name,
	#)

	if True: # restaurant.send_emails:
		from frappe.core.doctype.communication.email import make
		make(
			doctype=reservation.doctype,
			name=reservation.name,
			recipients=contact_email,
			sender='rm-erpnext@outlook.de',
			sender_full_name=restaurant.name,
			subject=email_template.subject,
			content=frappe.render_template(email_template.response, reservation.as_dict()),
			#attachments=attachments,
			send_email=1
		)
	
	frappe.db.commit() # Only necessary for testing

	return table_available



def get_table_allocations(restaurant, db_tables, db_reservations):
	return_reservations = []
	return_waiting_list = []

	tables_reservations = {table.name: frappe._dict({
		'name': table.name,
		'type': table.type,
		'min_seating': table.min_seating,
		'max_seating': table.max_seating,
		'reservation_mapping_priority': table.reservation_mapping_priority,
		'combinations': table.table_combinations.split(",") if table.type == 'Combined' else [],
		'reservations': []
	}) for table in db_tables}

	db_reservations = sorted(db_reservations, key= lambda x: (
		# Already assigned reservations have absolute priority
		(999 if x.assigned_tables is not None else 0) + \
		# Prioritize reservations that are already answered
		(2 if x.status == 'Accepted' else 1 if x.status == 'Waitlisted' else 0) * 10 + \
		# Prioritize larger reservations
		x.no_of_people * 1 + \
		# Prioritize longer reservations
		time_diff_in_hours(x.end_time, x.start_time) * 1 + \
		# Prioritize older reservations
		(time_diff_in_hours(frappe.utils.now(), x.creation) / 24) * 0.5
	), reverse=True)

	for reservation in db_reservations:
		assigned_tables = reservation.assigned_tables.split(",") if reservation.assigned_tables else None		

		if not assigned_tables:
			table_ranks = {}
			for table in tables_reservations.values():
				table_reservations = table.reservations
				for tc in table.combinations:
					table_reservations += tables_reservations[tc].reservations

				if (table.min_seating or 1) <= reservation.no_of_people <= table.max_seating and \
					not any([True for x in table_reservations if (reservation.start_time <= x.end_time and reservation.end_time >= x.start_time)]):

					# Calculate a rank for each table
					capacity_delta = table.max_seating - reservation.no_of_people

					# Type Delta
					type_delta = len(table.combinations) if table.type == 'Combined' else 5 if table.type == 'Reserved' else 0
					
					# Time Difference to reservations before
					reservations_before = [x.end_time for x in table.reservations if x.end_time < reservation.start_time and time_diff_in_hours(reservation.start_time, x.end_time) < (restaurant.default_duration_of_stay * 1.5)]
					reservation_before_delta = time_diff_in_hours(reservation.start_time, max(reservations_before)) if len(reservations_before) > 0 else 0

					# Time Difference to reservations after
					reservations_after = [x.start_time for x in table.reservations if x.start_time > reservation.end_time and time_diff_in_hours(x.start_time, reservation.end_time) < (restaurant.default_duration_of_stay * 1.5)]
					reservation_after_delta = time_diff_in_hours(min(reservations_after), reservation.end_time) if len(reservations_after) > 0 else 0

					# Sum up rank
					table_ranks[table.name] = 	(capacity_delta * 1) + \
												(type_delta * 1) + \
												((reservation_before_delta + reservation_after_delta) * 1) + \
												(table.reservation_mapping_priority * .1)
					
					# Break loop if rank is 0 since it can't get better than this
					if table_ranks[table.name] == 0:
						break

			if len(table_ranks) > 0:
				# Find Table with highest rank
				best_table = tables_reservations[min(table_ranks, key=table_ranks.get)]
				best_table.reservations.append(reservation)
				for table in best_table.combinations:
					tables_reservations[table].reservations.append(reservation)
				
				# Fill Dict for return value
				return_reservations.append(frappe._dict({
					'name': reservation.name,
					'restaurant_table': best_table.name
				}))

			else:
				return_waiting_list.append(reservation.name)

		else:
			for ass_table in assigned_tables:
				combi_table = tables_reservations[ass_table]
				combi_table.reservations.append(reservation)
				for table in combi_table.combinations:
					tables_reservations[table].reservations.append(reservation)
	
	return return_reservations, return_waiting_list
