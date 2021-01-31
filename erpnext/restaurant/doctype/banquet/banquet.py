# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import date_diff, today, getdate, add_days


class Banquet(Document):
	def validate(self):
		self.__validate_schedule()
		self.__validate_details()
		
	def __validate_schedule(self):
		if getdate(self.start_date) > getdate(self.end_date):
			frappe.throw(_("Start date cannot be after end date."))
		if self.option_date and getdate(self.option_date) >= getdate(self.start_date):
			frappe.throw(_("Option date must be before start date"))

	def __validate_details(self):
		for detail in self.banquet_details:
			if detail.start_time and detail.end_time:
				if getdate(detail.start_time) > getdate(detail.end_time):
					frappe.throw(_("Start date cannot be after end date (row {} in banquet details).").format(detail.idx))
				if getdate(detail.start_time) < getdate(self.start_date):
					frappe.throw(_("Row {}: Start time cannot be before start date of the banquet.").format(detail.idx))
				if getdate(detail.end_time) > add_days(getdate(self.end_date), 1):
					frappe.throw(_("Row {}: End time cannot be after end date of the banquet.").format(detail.idx))


	def before_save(self):
		self.__set_status()
		self.__calc_details()
	
	def __set_status(self):
		if self.docstatus == 0:
			self.status = 'Draft'
		elif self.docstatus == 1:
			self.status = 'Option'
		elif self.docstatus == 2:
			self.status = 'Cancelled'

	def __calc_details(self):

		current_section = None

		for detail in self.banquet_details:
			if current_section:
				# Set Section Time Frame
				if not current_section.start_time or getdate(current_section.start_time) > getdate(detail.start_time):
					current_section.start_time = detail.start_time
				if not current_section.end_time or getdate(current_section.end_time) < getdate(detail.end_time):
					current_section.end_time = detail.end_time

			if detail.type == 'Section Break':
				# Reset Current Section
				current_section = detail
				current_section.start_time = None
				current_section.end_time = None

			if detail.type in ['Section Break', 'Note']:
				 detail.linked_doc = None

