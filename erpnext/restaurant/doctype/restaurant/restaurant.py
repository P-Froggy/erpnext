# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class Restaurant(Document):

	def validate(self):
		if not 0.5 <= (self.default_duration_of_stay // 3600) <= 6:
			frappe.throw(_("Default duration of stay must be between 30 minutes and 6 hours."))
