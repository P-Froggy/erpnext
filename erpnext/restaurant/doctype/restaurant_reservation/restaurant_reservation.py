# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours, add_to_date
# Python Modules Import
import itertools # Chaining Lists


class RestaurantReservation(Document):
	def validate(self):
		self.validate_reservation()
		
	def validate_reservation(self):
		if not 0.5 <= time_diff_in_hours(self.end_time, self.start_time) < 12:
			frappe.throw(_("Reservations must have a duration of stay between 30 minutes and 12 hours."))

	def before_save(self):
		if not self.end_time:
			restaurant = frappe.get_doc('Restaurant', self.restaurant)
			self.end_time = add_to_date(self.start_time, seconds=restaurant.default_duration_of_stay)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def free_tables_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	tables = frappe.db.sql("""
		SELECT
			name AS `table`,
			type
		FROM `tabRestaurant Table`

		LEFT JOIN (
			SELECT
				reservation.name AS `reservation_name`,
				res_table.restaurant_table AS `reservation_table`
			FROM `tabRestaurant Reservation` reservation

			RIGHT JOIN `tabRestaurant Reservation Table` res_table
			ON res_table.parent = reservation.name
		) res
		ON res.reservation_table = name

		WHERE
			res.reservation_name IS NULL
		ORDER BY
			FIELD(type,'Standard','Combined','Reserve'),
			reservation_mapping_priority DESC

	""", as_dict=as_dict)

	# frappe.errprint(reservations)
	# frappe.errprint(tables)
	
	return tables

def check_availability(pax, restaurant, xxx):
	tables = frappe.db.get_list('Restaurant Table',
		filters={
			'restaurant': ['=', restaurant],
			'enabled': 1
		},
		fields=['max_seating', 'COUNT(max_seating) AS count'],
		order_by='max_seating DESC',
		group_by='max_seating',
		#start=10,
		#page_length=20,
		#as_list=True
	)
	reservations = frappe.db.get_list('Restaurant Reservation',
		filters={
			'restaurant': ['=', restaurant],
			'name': ['!=', xxx]
		},
		fields=['no_of_people', 'COUNT(no_of_people) AS count'],
		order_by='no_of_people DESC',
		group_by='no_of_people',
		#start=10,
		#page_length=20,
		#as_list=True
	)

	frappe.errprint({
		'tables': len(tables),
		'reservations': len(reservations),
		'tables d': tables,
		'reservations d': reservations
	})

	max_all = max(list(map(lambda y: y.no_of_people, reservations)) + [pax])

	delta_tables = {}
	for x in range(max_all, 0, -1):
		sum_tables = sum(i.count for i in tables if i.max_seating >= x)
		sum_reservations = sum(i.count for i in reservations if i.no_of_people >= x)
		if pax >= x:
			delta_tables[x] = (sum_tables - sum_reservations >= 1)
		else:
			delta_tables[x] = (sum_tables - sum_reservations >= 0)
		frappe.errprint("{}: {}".format(x, sum_tables - sum_reservations))

	frappe.errprint({
	'result': list(delta_tables.values())
	})
	
	return all(list(delta_tables.values()))



def get_tables():
	return frappe.db.sql("""
		SELECT
			tab.name,
			tab.type,
			tab.min_seating,
			tab.max_seating,
			tab.reservation_mapping_priority,
			GROUP_CONCAT(
				DISTINCT combi.restaurant_table
				ORDER BY combi.restaurant_table ASC
			) AS table_combinations
			
		FROM `tabRestaurant Table` tab

		LEFT JOIN `tabRestaurant Table Combination` combi
		ON combi.parent = tab.name

		WHERE
			tab.restaurant = 'Krusty Krab'
			AND tab.enabled = TRUE

		GROUP BY
			tab.name
	""", as_dict=True)

def get_reservations(restaurant, start_time, end_time):
	return frappe.db.sql("""
		SELECT
			res.name,
			res.no_of_people,
			res.start_time,
			res.end_time,
			GROUP_CONCAT(
				DISTINCT asg.restaurant_table
				ORDER BY asg.restaurant_table ASC
			) AS assigned_tables
			
		FROM `tabRestaurant Reservation` res

		LEFT JOIN `tabRestaurant Reservation Table` asg
		ON asg.parent = res.name

		WHERE
			res.docstatus = 1
			AND res.restaurant = %(restaurant)s
			AND res.start_time <= %(end_time)s
			AND res.end_time >= %(start_time)s

		GROUP BY
			res.name
	""", {
			'restaurant': restaurant,
			'start_time': start_time,
			'end_time': end_time
		}, as_dict=True)

def format_response(assigned, waiting_list, skipped):
	return """
		<strong>Assigned</strong><br/>
		{0}<br/>
		<strong>Not assigned</strong><br/>
		{1}<br/>
		<strong>Skipped</strong><br/>
		{2}
	""".format("<br/>".join(map(lambda x: "{0}: {1}".format(x, assigned[x]), assigned)), "<br/>".join(waiting_list), "<br/>".join(skipped))



# --------------------- New
@frappe.whitelist()
def assign_tables(restaurant, start_time, end_time, save=False):
	# Validate
	if time_diff_in_hours(end_time, start_time) < 0.5:
		frappe.throw(_("The period for automatic assignment of reservations must be at least 30 minutes long."))
	#if start_time < frappe.utils.now():
	#	frappe.throw(_("The start date cannot be in the past."))

	db_tables = get_tables()
	db_reservations = sorted(get_reservations(restaurant=restaurant, start_time=start_time, end_time=end_time), key=lambda x: 1 if x.assigned_tables else 0, reverse=True)
	reservations, waiting_list = get_auto_assignments(db_tables, db_reservations)
	
	for reservation in reservations:
		if save == True:
			# Append assigned table child row
			doc = frappe.get_doc('Restaurant Reservation', reservation.name)
			doc.status = 'Accepted'
			doc.append("assigned_tables", {"restaurant_table": reservation.restaurant_table})
			doc.save(ignore_permissions=True, ignore_version=True)
			doc.add_comment('Label', _("assigned table {} through auto-assignment").format(frappe.bold(reservation.restaurant_table)))

		frappe.errprint("{0}: {1}".format(reservation.name, reservation.restaurant_table))
	frappe.errprint("Waiting List: {0}".format(", ".join([x.name for x in waiting_list])))


def get_auto_assignments(db_tables, db_reservations):
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


	for reservation in db_reservations:
		assigned_tables = reservation.assigned_tables.split(",") if reservation.assigned_tables else None

		if not assigned_tables:
			table_ranks = {}
			for table in tables_reservations.values():
				table_reservations = list(itertools.chain(table.reservations, *[x.reservations for name, x in tables_reservations.items() if name in x.combinations])) if table.type == 'Combined' else table.reservations

				if (table.min_seating or 1) <= reservation.no_of_people <= table.max_seating and \
					not any([True for x in table_reservations if (reservation.start_time <= x.end_time and reservation.end_time >= x.start_time)]):

					# Calculate a rank for each table
					capacity_delta = table.max_seating - reservation.no_of_people

					# Type Delta
					type_delta = len(table.combinations) if table.type == 'Combined' else 5 if table.type == 'Reserved' else 0
					
					# Time Difference to reservations before
					reservations_before = [x.end_time for x in table.reservations if x.end_time < reservation.start_time and time_diff_in_hours(reservation.start_time, x.end_time) < 3]
					reservation_before_delta = time_diff_in_hours(reservation.start_time, max(reservations_before)) if len(reservations_before) > 0 else 0

					# Time Difference to reservations after
					reservations_after = [x.start_time for x in table.reservations if x.start_time > reservation.end_time and time_diff_in_hours(x.start_time, reservation.end_time) < 3]
					reservation_after_delta = time_diff_in_hours(min(reservations_after), reservation.end_time) if len(reservations_after) > 0 else 0

					# Sum up rank
					table_ranks[table.name] = 	(capacity_delta * 1) + \
												(type_delta * 1) + \
												((reservation_before_delta + reservation_after_delta) * 1) + \
												(table.reservation_mapping_priority * .1)


			if len(table_ranks) > 0:
				# Find Table with highest rank
				best_table = next(x for x in tables_reservations.values() if x.name == min(table_ranks, key=table_ranks.get))
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
