from __future__ import unicode_literals
from frappe import _

def get_data():
	return [	
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Item Commission",
					"description":_("Item Commission"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "PAV Healthcare Settings",
					"description":_("PAV Healthcare Settings"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Sales Partner",
					"description":_("Sales Partner"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Sales Partner Marketer",
					"description":_("Sales Partner Marketer"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Healthcare Practitioner",
					"description":_("Healthcare Practitioner"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description":_("Sales Invoice"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Patient Medical Record",
					"description":_("Patient Medical Record"),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Commission"),
			"items": [
				{
					"type": "doctype",
					"name": "Commission Compute",
					"description":_("Commission Compute"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Commission Compute HP",
					"description":_("Commission Compute HP"),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Item Commission Report",
					"doctype": "Item Commission",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance for Party in Party Currency",
					"doctype": "Item Commission",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Duplicated Patient Medical Record",
					"doctype": "Patient Medical Record",
					"is_query_report": True
				},
			]
		},
	]
