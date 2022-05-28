// Copyright (c) 2021, Partner Consulting Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Commission Compute', {
	refresh(frm) {

		frm.events.show_general_ledger(frm);
	},
	mode_of_payment: function (frm) {
		frappe.call({
			method: "pav_healthcare.pav_healthcare.doctype.commission_compute.commission_compute.get_payment_account",
			args: {
				"mode_of_payment": frm.doc.mode_of_payment,
				"company": frm.doc.company
			},
			callback: function (r) {
				if (r.message) {
					if (r.message.account_currency != frm.doc.transaction_currency)
						frappe.throw("Cash/Bank Account not same Transaction Currency")
					cur_frm.set_value("cash_bank_account", r.message.account);
					frm.refresh_fields();
					cur_frm.refresh_field('currency');
				} else {
					frm.set_value("cash_bank_account", "");

					frm.refresh_fields();
					return;
				}
			}
		});
	},
	show_general_ledger: function (frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Genral Ledger'), function () {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
					group_by: ""
				};
				frappe.set_route("query-report", "General Ledger");
			}, "fa fa-table");
		}
	},

	get_commission: function (frm) {
		cur_frm.clear_table("items");

		frm.events.fill_commission(frm);
	},
	


	fill_commission: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_commission',
			callback: function (r) {
				if (r.docs[0].items) {
					frm.save();
					frm.refresh();

				}
			}
		});
	},
	calc_parties: function (frm) {
		console.log("hiiii")
		cur_frm.clear_table("parties");
		return frappe.call({
			doc: frm.doc,
			method: 'calc_parties',
			callback: function (r) {
				if (r.docs[0].parties) {
					frm.save();
					frm.refresh();

				}
			}
		});
	}
});


