# -*- coding: utf-8 -*-
# Copyright (c) 2022, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class SalesInvoiceItemStatus(Document):
	def validate(self):
		if not self.is_new():
			enable_sales_invoice_item_status=frappe.db.get_single_value("PAV Healthcare Settings", "enable_sales_invoice_item_status")
			if enable_sales_invoice_item_status:
				enable_roles=frappe.db.get_single_value("PAV Healthcare Settings", "enable_roles")
				if enable_roles:
					cartoon_film_status,laser_film_status,cd_status,dvd_status,delivery_status=\
						frappe.db.get_value(self.doctype,{"name":self.name},\
						["cartoon_film_status","laser_film_status","cd_status","dvd_status","delivery_status"])

					if self.cartoon_film_status!=cartoon_film_status or self.laser_film_status!=laser_film_status\
						or self.cd_status!=cd_status or self.dvd_status!=dvd_status:
						technical_role=frappe.db.get_single_value("PAV Healthcare Settings", "technical_role")
						if technical_role:
							if not technical_role in frappe.get_roles(frappe.session.user):
								frappe.throw(_("You have no permission, please ask System Manager give you"))
						else:
							frappe.throw(_("There is no Technical Role in Settings, please ask System Manager assign role"))

					if self.delivery_status!=delivery_status:
						reception_role=frappe.db.get_single_value("PAV Healthcare Settings", "reception_role")
						if reception_role:
							if not reception_role in frappe.get_roles(frappe.session.user):
								frappe.throw(_("You have no permission, please ask System Manager give you"))
						else:
							frappe.throw(_("There is no Reception Role in Settings, please ask System Manager assign role"))		