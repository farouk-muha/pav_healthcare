# -*- coding: utf-8 -*-
# Copyright (c) 2021, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _, throw
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from frappe.utils import cint, cstr, formatdate, flt, getdate, nowdate, get_link_to_form
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries
from erpnext.controllers.accounts_controller import AccountsController
from collections import defaultdict, OrderedDict

class CommissionComputeHP(AccountsController):
	def validate(self):
		if self.is_paid and not self.cash_bank_account:
			frappe.throw("Cash/Bank Account is Mandatory")
		self.calc_total_parties()

	def on_submit(self):
		self.make_gl_entries()
		self.update_commission_check(cancel=False)
	
		# self.create_log()
	def before_cancel(self):
		self.update_commission_check(cancel=True)

	def update_commission_check(self,cancel=True):
		for item in self.get('items'):
			if item.patient_medical_record:
				doc = frappe.get_doc('Patient Medical Record',item.patient_medical_record)				
				if cancel==False:
					doc.db_set("is_accrual", 1, update_modified=False)					
				else:					
					doc.db_set("is_accrual", 0, update_modified=False)
					

	def on_cancel(self):
		self.make_gl_entries(cancel=True)
	
	def calc_total_parties(self):
		self.amount=0
		self.additional_amount=0
		self.total_amount=0
		for row in self.get("parties"):
			row.total_amount=0
			if row.amount:
				self.amount+=row.amount
				row.total_amount+=row.amount
			if row.additional_amount:
				self.additional_amount+=row.additional_amount			
				row.total_amount += row.additional_amount						
		self.total_amount=self.amount+self.additional_amount

	def make_gl_entries(self, cancel = False):
		gl_entries=[]
		self.make_commissions_gl_entry(gl_entries,mark_as_calc=cancel)
		if gl_entries:
			make_gl_entries(gl_entries, cancel = cancel)

	def make_commissions_gl_entry(self, gl_entries,mark_as_calc=True):
		
		

		for row in self.get("items"):
			# doc = frappe.get_doc('Sales Invoice Item',row.sii_no)
			total=0.0
			if row.healthcare_practitioner_amount!=0.0 and row.healthcare_practitioner:
				# doc.db_set("internal", mark_as_calc, update_modified=False)
				# gl_entries.append(
				# 	self.get_gl_dict({
				# 		"posting_date":self.posting_date,
				# 		"account": self.healthcare_practitioner_account,
				# 		"party_type": "Healthcare Practitioner",
				# 		"party": row.healthcare_practitioner,						
				# 		"credit": flt((row.healthcare_practitioner_amount*self.exchange_rate),2),
				# 		"credit_in_account_currency": flt((row.healthcare_practitioner_amount),2),
				# 		"account_currency":self.transaction_currency,
				# 		"against_voucher": self.name,
				# 		"against_voucher_type": self.doctype,						
				# 		"cost_center": row.cost_center
				# 	}, item=self))
				# if self.is_paid:
				# 	gl_entries.append(
				# 	self.get_gl_dict({
				# 		"posting_date":self.posting_date,
				# 		"account": self.healthcare_practitioner_account,
				# 		"party_type": "Healthcare Practitioner",
				# 		"party": row.healthcare_practitioner,						
				# 		"debit": flt((row.healthcare_practitioner_amount*self.exchange_rate),2),
				# 		"debit_in_account_currency": flt((row.healthcare_practitioner_amount),2),
				# 		"account_currency":self.transaction_currency,
				# 		"against_voucher": self.name,
				# 		"against_voucher_type": self.doctype,						
				# 		"cost_center": row.cost_center
				# 	}, item=self))
				total+=flt(( row.healthcare_practitioner_amount),2)
				if total!=0.0:		
					gl_entries.append(
						self.get_gl_dict({
							"posting_date":self.posting_date,
							"account": row.item_account,
							"account_currency":self.transaction_currency,
							"debit": flt((total*self.exchange_rate),2),
							"debit_in_account_currency": flt((total),2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,						
							"cost_center": row.cost_center
						}, item=self))
		if self.additional_amount>0:
			gl_entries.append(
				self.get_gl_dict({
					"posting_date":self.posting_date,
					"account": self.additional_amount_account,
					"account_currency":self.transaction_currency,
					"debit": flt((self.additional_amount*self.exchange_rate),2),
					"debit_in_account_currency": flt((self.additional_amount),2),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center
				}, item=self))
		for row in self.get("parties"):
			gl_entries.append(
				self.get_gl_dict({
					"posting_date":self.posting_date,
					"account": self.healthcare_practitioner_account,
					"party_type": "Healthcare Practitioner",
					"party": row.party,						
					"credit": flt((row.total_amount*self.exchange_rate),2),
					"credit_in_account_currency": flt((row.total_amount),2),
					"account_currency":self.transaction_currency,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,						
				}, item=self))
			if self.is_paid:
				gl_entries.append(
				self.get_gl_dict({
					"posting_date":self.posting_date,
					"account": self.healthcare_practitioner_account,
					"party_type": "Healthcare Practitioner",
					"party": row.party,						
					"debit": flt((row.total_amount*self.exchange_rate),2),
					"debit_in_account_currency": flt((row.total_amount),2),
					"account_currency":self.transaction_currency,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,						
				}, item=self))

		if self.is_paid:
			gl_entries.append(
			self.get_gl_dict({
				"posting_date":self.posting_date,
				"account": self.cash_bank_account,
				"account_currency":self.transaction_currency,
				"credit": flt((self.total_amount*self.exchange_rate),2),
				"credit_in_account_currency": flt((self.total_amount),2),
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,						
				"cost_center": self.cost_center,
				"remarks":self.remarks or ''
			}, item=self))
		# frappe.msgprint("gl_entries={0}".format(gl_entries))

	def get_commissions_list(self):
		condition = ''
		if self.healthcare_practitioner:
			condition = """ and pmr.practitioner = '%(healthcare_practitioner)s'"""% {"healthcare_practitioner": self.healthcare_practitioner}
		return frappe.db.sql("""select pmr.name as patient_medical_record, pmr.practitioner as healthcare_practitioner,
		si.patient,si.patient_name,si.customer,si.customer_name,
		si.name as sale,sii.item_code,sii.item_name,sii.qty,sii.rate,sii.income_account,sii.cost_center,		
		sii.name as sii_no

		from `tabPatient Medical Record` pmr
		
		INNER JOIN  `tabSales Invoice` si 
		ON pmr.sales_invoice=si.name

		INNER JOIN `tabSales Invoice Item` sii		
		ON si.name=sii.parent

		INNER JOIN  `tabAccount` acc
		ON sii.income_account=acc.name
		
		where pmr.docstatus=1 and si.docstatus=1 and pmr.item=sii.item_code and pmr.is_accrual=0 and si.currency=%s and acc.account_currency=%s and pmr.date >= %s and pmr.date <= %s  
		{condition}
		HAVING si.name is not null and sii.name is not null
		""".format(condition=condition),[self.transaction_currency,self.transaction_currency,self.from_date,self.to_date], as_dict=True)

	def get_exchange_rate(self):
		return frappe.db.sql("""select exchange_rate as rate
			from `tabCurrency Exchange`
			where from_currency= %s and to_currency= %s order by date desc limit 1 """,
			[self.transaction_currency,self.c_currency], as_dict=True)

	def fill_commission(self):
		self.items=None
		self.parties=None
		parties_row = {}
		data=[]
		self.transaction_currency=frappe.db.get_single_value("PAV Healthcare Settings", "transaction_currency")
		exchange_rate=self.get_exchange_rate()
		self.exchange_rate=exchange_rate[0].rate
		# frappe.msgprint(transaction_currency)
		commissions = self.get_commissions_list()
		if not commissions:
				frappe.msgprint(_("No commissions"))
		for d in commissions:
			row=self.append('items', {})
			row.transaction_currency=self.transaction_currency
			row.patient_medical_record=d.patient_medical_record
			row.sales_invoice=d.sale			
			row.item_code=d.item_code
			row.item_name=d.item_name
			row.qty=d.qty
			row.amount=d.rate
			row.patient=d.patient
			row.patient_name=d.patient_name
			row.customer=d.customer
			row.customer_name=d.customer_name
			row.sii_no=d.sii_no
			# if not d.external:
				
			# if not d.internal:
				
			details=get_item_detail(self.company,d.item_code)
			# frappe.msgprint(frappe.as_json(details))
			row.item_account=d.income_account
			row.item_group=details['item_group']
			row.cost_center=d.cost_center
			# row.project=details['project']
			
			row.healthcare_practitioner_amount=0.0
			
			
			if d.healthcare_practitioner:
				row.healthcare_practitioner=d.healthcare_practitioner
				rate=get_item_commission(item=d.item_code,item_group=row.item_group,party=d.healthcare_practitioner,party_type='Healthcare Practitioner')
				# row.internal_party_amount=flt(n*self.exchange_rate)
				row.healthcare_practitioner_amount=flt(rate*row.qty)
				roww="{0}-{1}".format('Healthcare Practitioner',d.healthcare_practitioner)
				if roww not in parties_row:
					parties_row[roww] = {}
					parties_row[roww].setdefault(roww)
					parties_row[roww]["party_type"] = 'Healthcare Practitioner'
					parties_row[roww]["party"] = d.healthcare_practitioner
					parties_row[roww]["amount"] = rate
				else:
					parties_row[roww]["amount"] = parties_row[roww]["amount"] + rate
				# frappe.throw(parties_row)
			
			# frappe.msgprint("{0},{1}.{2}".format(row.internal_amount,row.sales_partner_amount,row.market_amount))
			row.total_commission=row.healthcare_practitioner_amount
			row.remaining_amount=row.amount-row.total_commission
			
		
		self.healthcare_practitioner_account=frappe.db.get_single_value("PAV Healthcare Settings", "healthcare_practitioner_account")
		self.additional_amount_account=frappe.db.get_single_value("PAV Healthcare Settings", "additional_amount_account")
		self.cost_center=frappe.db.get_single_value("PAV Healthcare Settings", "default_cost_center")
		
		for party in sorted(parties_row):
			p = parties_row.get(party)
			# frappe.msgprint(p.get('party'))
			row=self.append('parties', {})
			row.party_type=p.get('party_type')
			row.party=p.get('party')
			row.amount=p.get('amount')
		# frappe.throw(parties_row)
		self.save()		
		self.reload()

# def get_marketer(dr):
# 	return frappe.db.sql("""select sales_partner_marketer from `tabSales Partner` where partner_type='Doctor'
# 	and name=%s 
# 	""",dr, as_dict=True)

def get_item_commission(item=None,item_group=None, party=None,partner_type=None,party_type=None):
	# it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item=%s and party is null and partner_type is null and party_type is null and disabled=0 limit 1""",[item])	
	it_doc=None
	# if not it_doc and item:
	# 	it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and disabled=0 limit 1""",[item])
	# if not it_doc and item_group:
	# 	it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and disabled=0 limit 1""",[item_group])
	# frappe.throw("{0}-{1}-{2}".format(item,party,party_type))
	if not it_doc and item and party and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party=%s and party_type=%s and disabled=0 limit 1""",[item,party,party_type])
	if not it_doc and item_group and party and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party=%s and party_type=%s and disabled=0 limit 1""",[item_group,party,party_type])
	if not it_doc and item and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party_type = %s and party is null and disabled=0 limit 1""",[item,party_type])
	if not it_doc and item_group and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party_type = %s and party is null and disabled=0 limit 1""",[item_group,party_type])
	if not it_doc and item:
		it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party is null and party_type is null and disabled=0 limit 1""",[item])	
	if not it_doc and item_group:
		it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party is null and party_type is null and disabled=0 limit 1""",[item_group])	

	
	rate=0.0
	if it_doc:
		rate=it_doc[0][0]
	# frappe.msgprint("rate={0}".format(rate))
	return rate



def get_item_details(args=None):
	item = frappe.db.sql("""select i.name,i.item_group
			from `tabItem` i 
			where i.name=%s """,(args.get('item_code')), as_dict = True)
	if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

	return item[0]

from erpnext.accounts.utils import get_company_default

@frappe.whitelist()
def get_item_detail(company,item_code):
	item_dict = {}
	item_details = get_item_details({'item_code': item_code, 'company': company})
	# item_dict['income_account'] = (item_details.get("income_account") or get_item_group_defaults(item_code, company).get("income_account") or 
			# get_company_default(company, "default_income_account") or frappe.get_cached_value('Company',  company, 
			# "default_income_account"))
	item_dict['item_group']=item_details.get('item_group')
	# item_dict['cost_center'] = item_details.get('income_cost_center')
	return item_dict

@frappe.whitelist()
def get_payment_account(mode_of_payment, company):
	account = frappe.db.get_value("Mode of Payment Account",
		{"parent": mode_of_payment, "company": company}, "default_account")
	if not account:
		frappe.throw(_("Please set default account in Mode of Payment {0}")
			.format(mode_of_payment))

	return {
		"account": account,
		"account_currency": frappe.db.get_value("Account", {"name": account}, "account_currency")
	}