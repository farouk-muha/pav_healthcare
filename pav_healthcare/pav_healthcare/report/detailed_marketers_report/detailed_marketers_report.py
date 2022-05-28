# Copyright (c) 2022, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_column(filters)
	data = []
	cond = ""
	if filters.get("sales_partner_name"):
		cond +=' and s.sales_partner_name= %(sales_partner_name)s'
	if filters.get("sales_marketer_name"):
		cond +=' and s.sales_marketer_name= %(sales_marketer_name)s'
	if filters.get("status"):
		cond +=' and s.status= %(status)s'
	if filters.get("item_group"):
		cond +=' and si.item_group= %(item_group)s'

	data=frappe.db.sql("""select
			s.patient_name ,s.sales_partner_name ,s.sales_marketer_name, s.status,
			si.item_name,si.item_group,si.qty,si.net_rate
		from
			`tabSales Invoice` s
		JOIN  
			`tabSales Invoice Item` si on s.name = si.parent
		WHERE 
			s.posting_date between %(from_date)s and %(to_date)s and s.docstatus = 1
			{0}
		""".format(cond), filters, as_dict=True)
	
	return columns, data

def get_column(filters):
	columns = [
	{
			"fieldname":"sales_partner_name",
			"label": _("Sales Partner Name"),
			"fieldtype": "Data",
		"width": 150
			
	},

	{
		"fieldname": "sales_marketer_name",
		"label": _("Marketer Name"),
		"fieldtype":"Data",
		"width": 120
	},
	{
		"fieldname": "item_name",
		"label": _("Item Name"),
		"fieldtype":"Data",
		"width": 180
	},
	{
		"fieldname": "item_group",
		"label": _("Item Group"),
		"fieldtype":"Data",
		"width": 180
	},
	{
		"fieldname": "qty",
		"label": _("Quantity"),
		"fieldtype":"Data",
		"width": 60
	},
	{
		"fieldname": "net_rate",
		"label": _("Net Rate"),
		"fieldtype":"Currency",
		"width": 120
	},
	{
		"fieldname": "patient_name",
		"label": _("Patient Name"),
		"fieldtype": "Data",
		"width": 150
	},
	]
	

	return columns


