# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, re
from frappe.model.document import Document

class RestaurantTable(Document):
	def validate(self):
		if self.max_seating < self.min_seating:
			frappe.throw(_("Maximum seating has to be equal are larger than minimum seating."))	

	def autoname(self):
		prefix = re.sub('-+', '-', self.restaurant.replace(' ', '-'))
		self.name = "{0}-{1}".format(prefix, self.table_no)
		
		# Original Function:
		#prefix = re.sub('-+', '-', self.restaurant.replace(' ', '-'))
		#self.name = make_autoname(prefix + '-.##')
	
	@frappe.whitelist()
	def rename_doc(self, restaurant, table_no, merge=0):
		#self.restaurant = restaurant
		#self.table_no = table_no
		self.db_set('restaurant', restaurant)
		self.db_set('table_no', table_no)
		#self.save(ignore_permissions=True, ignore_version=True)

		prefix = re.sub('-+', '-', self.restaurant.replace(' ', '-'))
		new_name = "{0}-{1}".format(prefix, self.table_no)
		if new_name != self.name:
			frappe.rename_doc("Restaurant Table", self.name, new_name, force=1, merge=merge)
			return new_name
