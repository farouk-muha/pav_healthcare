// Copyright (c) 2016, Partner Consulting Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Duplicated Patient Medical Record"] = {
	"filters": [
		{
			"fieldname":"to_dDate",
			"label": __("From Date"),
			"fieldtype": "Date"			
		},
		{
			"fieldname":"from_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname":"healthcare_practitioner",
			"label": __("Healthcare Practitioner"),
			"fieldtype": "Link",
			"options": "Healthcare Practitioner",
		},
	]
};
