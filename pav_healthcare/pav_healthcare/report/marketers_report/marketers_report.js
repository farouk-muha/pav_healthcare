// Copyright (c) 2016, Partner Consulting Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Marketers Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"label": __("TO Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd":1			
		},
		{
			"fieldname":"sales_partner_name",
			"label": __("Sales Partner Name"),
			"fieldtype": "Link",
			"options": 'Sales Partner',
		
			
		},
		{
			"fieldname":"sales_marketer_name",
			"label": __("marketer name"),
			"fieldtype": "Data",
		
			
		},
		{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": [,'Paid','Overdue']
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": 'Item Group',
		},

	]
};
