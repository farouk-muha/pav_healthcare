# -*- coding: utf-8 -*-
# Copyright (c) 2021, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class ItemCommission(Document):
	def validate(self):
		if self.item_type=='Item':
			self.item_name = frappe.db.get_value("Item", self.item, 'item_name')
		elif self.item_type=='Item Group':
			self.item_name = self.item
		if not self.party:
			self.title="{0} ({1})".format(self.party_type,self.item_name)
		else:
			self.title="{0} ({1})".format(_(self.party),self.item_name)
		filters={"item_type":self.item_type,"item": self.item,"party_type":self.party_type}
		if self.party:
			filters.update({
				"party": self.party
			})
		else:
			filters.update({
				"party": ('is','not set')
			})
		if not self.get('__islocal'):
			filters.update({
				"name": ('!=',self.name)
			})
		res=frappe.get_list("Item Commission", fields=["name"] ,filters=filters, order_by= "name asc")
		if (self.get('__islocal') and res) or (not self.get('__islocal') and len(res)>0):
			frappe.throw("Already Exist {0}".format(res))

