# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def tables_query2(restaurant):
	return frappe.db.get_list('Restaurant Table',
		filters={
			'restaurant': restaurant,
			'enabled': 1
		},
		fields=[
			'name',
			'type',
			'min_seating',
			'max_seating',
			'reservation_mapping_priority',
			'json_arrayagg(`tabRestaurant Table Combination`.restaurant_table) AS table_combinations'
		],
		#order_by='date desc',
		group_by='name',
		#start=10,
		#page_length=20,
		#as_list=True
	)

def tables_query(restaurant):
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
			tab.restaurant = %(restaurant)s
			AND tab.enabled = TRUE

		GROUP BY
			tab.name
	""", {'restaurant': restaurant}, as_dict=True)

def reservations_query(restaurant, start_time, end_time):
	return frappe.db.sql("""
		SELECT
			res.name,
			res.restaurant,
			res.no_of_people,
			res.start_time,
			res.end_time,
			GROUP_CONCAT(
				DISTINCT asg.restaurant_table
				ORDER BY asg.restaurant_table ASC
			) AS assigned_tables,
			res.creation
			
		FROM `tabRestaurant Reservation` res

		LEFT JOIN `tabRestaurant Reservation Table` asg
		ON asg.parent = res.name

		WHERE
			res.docstatus = 1
			AND res.status NOT IN ('Rejected', 'NoShow', 'Completed', 'Cancelled')
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


# Depreciated, delete if possible
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