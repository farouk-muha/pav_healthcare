# Copyright (c) 2013, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cint
from frappe import _


def execute(filters=None):
	columns, data = [], []

	columns = get_columns()
	conditions = get_conditions(filters)
	data = get_data(filters, conditions)

	return columns, data

def get_conditions(filters):
	conditions = []
	conditions.append("docstatus < 2")
	if filters.get("from_date"): 
		conditions.append("date >= %(from_date)s")
	if filters.get("to_date"): 
		conditions.append("date <= %(to_date)s")
	if filters.get("healthcare_practitioner"): 
		conditions.append("practitioner = %(healthcare_practitioner)s")
		
	return " where {}".format(" and ".join(conditions)) if conditions else ""

def get_data(filters, conditions):
	data = frappe.db.sql("""
		SELECT sales_invoice, item, count(name) as dublicate_count
		FROM
			`tabPatient Medical Record`	
		{0}
			group by sales_invoice, item 
			HAVING COUNT(name) > 1
			order by sales_invoice desc """.format(conditions), filters, as_dict=1)

	return data

def get_columns():	
	columns = [
	{
		"fieldname": "sales_invoice",
		"label": _("Sales Invoice"),
		"fieldtype": "Link",
		"options": "Sales Invoice",
		"width": 100
	},
	{
		"fieldname": "item",
		"label": _("Item"),
		"fieldtype": "Link",
		"options": "Item",		
		"width": 100
	},
	{
		"fieldname": "dublicate_count",
		"label": _("Dublicate Count"),
		"fieldtype": "Int",
		"width": 100
	},
	]

	return columns