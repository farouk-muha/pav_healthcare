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

class CommissionCompute(AccountsController):
	def validate(self):
		if self.round_off_account:
			self.round_off_account=frappe.get_value("Company",self.company,"write_off_account")
		if self.is_paid and not self.cash_bank_account:
			frappe.throw("Cash/Bank Account is Mandatory")
		# self.calc_total_items()
		# self.calc_parties()
		self.calc_total_parties()

	def on_submit(self):
		self.make_gl_entries()
		self.update_commission_check(cancel=False)
	
		# self.create_log()
	def before_cancel(self):
		self.update_commission_check(cancel=True)

	def update_commission_check(self,cancel=True):
		for item in self.get('items'):
			if item.sii_no:
				doc = frappe.get_doc('Sales Invoice Item',item.sii_no)				
				if cancel==False:
					doc.db_set("is_accrual", 1, update_modified=False)					
				else:					
					doc.db_set("is_accrual", 0, update_modified=False)
					

	def on_cancel(self):
		self.make_gl_entries(cancel=True)

	def calc_parties(self):
		self.calc_total_items()
		self.parties=None
		self.amount=0
		self.additional_amount=0
		self.total_amount=0
		parties_row = {}
		for row in self.get("items"):
			if row.sales_partner and row.sales_partner_amount:
				self.amount+=row.amount
				roww_sales_partner="{0}-{1}".format('Sales Partner',row.sales_partner)
				if roww_sales_partner not in parties_row:
					parties_row[roww_sales_partner] = defaultdict(dict)
					parties_row[roww_sales_partner]["party_type"] = 'Sales Partner'
					parties_row[roww_sales_partner]["party"] = row.sales_partner
					parties_row[roww_sales_partner]["amount"] = row.sales_partner_amount
				else:
					parties_row[roww_sales_partner]["amount"] = parties_row[roww_sales_partner]["amount"] + row.sales_partner_amount
							
			if row.sales_partner_marketer and row.sales_partner_marketer_amount:
				roww_sales_partner_marketer="{0}-{1}".format('Sales Partner Marketer',row.sales_partner_marketer)			
				if roww_sales_partner_marketer not in parties_row:
					parties_row[roww_sales_partner_marketer] = defaultdict(dict)
					parties_row[roww_sales_partner_marketer]["party_type"] = 'Sales Partner Marketer'
					parties_row[roww_sales_partner_marketer]["party"] = row.sales_partner_marketer
					parties_row[roww_sales_partner_marketer]["amount"] = row.sales_partner_marketer_amount
				else:
					parties_row[roww_sales_partner_marketer]["amount"] = parties_row[roww_sales_partner_marketer]["amount"] + row.sales_partner_marketer_amount

		for party in sorted(parties_row):
			p = parties_row.get(party)
			# frappe.msgprint(p.get('party'))
			row=self.append('parties', {})
			row.party_type=p.get('party_type')
			row.party=p.get('party')
			row.amount=p.get('amount')

		self.total_amount=self.amount+self.additional_amount
		self.save()
		self.reload()

	def calc_total_items(self):
		for row in self.get("items"):
			row.total_commission=0
			if row.sales_partner_amount and row.sales_partner_marketer_amount:
				row.total_commission=row.sales_partner_amount+row.sales_partner_marketer_amount
			elif row.sales_partner_amount and not row.sales_partner_marketer_amount:
				row.total_commission=row.sales_partner_amount
			elif not row.sales_partner_amount and row.sales_partner_marketer_amount:
				row.total_commission=row.sales_partner_marketer_amount
			row.remaining_amount=row.amount-row.total_commission

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
		self.make_commissions_gl_entry(gl_entries,cancel = cancel)
		if gl_entries:
			make_gl_entries(gl_entries, cancel = cancel)

	def make_commissions_gl_entry(self, gl_entries,cancel = False):
		for row in self.get("items"):
			doc = frappe.get_doc('Sales Invoice Item',row.sii_no)	
			if cancel==False:
				doc.db_set("is_accrual", 1, update_modified=False)					
			else:					
				doc.db_set("is_accrual", 0, update_modified=False)		
			if row.total_commission>0:		
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": row.item_account,
						"account_currency":self.transaction_currency,
						"debit": flt((row.total_commission*self.exchange_rate),2),
						"debit_in_account_currency": flt((row.total_commission),2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
						"cost_center": row.cost_center
					}, item=self))
			if row.sales_partner_amount!=0.0 and row.sales_partner:
				# doc.db_set("external", mark_as_calc, update_modified=False)
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_account,
						"party_type": "Sales Partner",
						"party": row.sales_partner,						
						"credit": flt((row.sales_partner_amount*self.exchange_rate),2),
						"credit_in_account_currency":flt(( row.sales_partner_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
						"cost_center": row.cost_center
					}, item=self))
				if self.is_paid:
					gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_account,
						"party_type": "Sales Partner",
						"party": row.sales_partner,						
						"debit": flt((row.sales_partner_amount*self.exchange_rate),2),
						"debit_in_account_currency":flt(( row.sales_partner_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
						"cost_center": row.cost_center
					}, item=self))
			if row.sales_partner_marketer_amount!=0.0 and row.sales_partner_marketer:
				# doc.db_set("marketer", mark_as_calc, update_modified=False)
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_marketer_account,
						"party_type": "Sales Partner Marketer",
						"party": row.sales_partner_marketer,						
						"credit": flt((row.sales_partner_marketer_amount*self.exchange_rate),2),
						"credit_in_account_currency": flt((row.sales_partner_marketer_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
						"cost_center": row.cost_center
					}, item=self))	
				if self.is_paid:
					gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_marketer_account,
						"party_type": "Sales Partner Marketer",
						"party": row.sales_partner_marketer,						
						"debit": flt((row.sales_partner_marketer_amount*self.exchange_rate),2),
						"debit_in_account_currency": flt((row.sales_partner_marketer_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
						"cost_center": row.cost_center
					}, item=self))	
		for row in self.get("parties"):
			if row.additional_amount:
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_account if row.party_type=='Sales Partner' else self.sales_partner_marketer_account,
						"party_type": row.party_type,
						"party": row.party,						
						"credit": flt((row.additional_amount*self.exchange_rate),2),
						"credit_in_account_currency": flt((row.additional_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
					}, item=self))
				if self.is_paid:
					gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.sales_partner_account if row.party_type=='Sales Partner' else self.sales_partner_marketer_account,
						"party_type": row.party_type,
						"party": row.party,						
						"debit": flt((row.additional_amount*self.exchange_rate),2),
						"debit_in_account_currency": flt((row.additional_amount),2),
						"account_currency":self.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,						
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
					"cost_center": self.cost_center
				}, item=self))
		if self.round_off_account and self.round_off_amount:
			gl_entries.append(
				self.get_gl_dict({
					"posting_date":self.posting_date,
					"account": self.round_off_account,
					"account_currency":self.c_currency,
					"credit": flt((self.round_off_amount),2),
					"credit_in_account_currency": flt((self.round_off_amount),2),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,						
					"cost_center": self.cost_center
				}, item=self))
		# frappe.msgprint("gl_entries={0}".format(gl_entries))

	def get_commissions_list(self):
		
		return frappe.db.sql("""select si.patient,si.patient_name,si.customer,si.customer_name,
		si.name as sale,sii.item_code,sii.item_name,sii.qty,sii.rate as rate,si.sales_partner_name,sii.income_account,sii.cost_center,	
		sii.name as sii_no,sp.sales_partner_marketer
		
		from `tabSales Invoice Item` sii
		INNER JOIN  `tabSales Invoice` si 
		ON sii.parent=si.name
		INNER JOIN  `tabSales Partner` sp
		ON si.sales_partner_name=sp.name

		INNER JOIN  `tabAccount` acc
		ON sii.income_account=acc.name

		INNER JOIN  `tabItem` item
		ON sii.item_code=item.name
		
		where sii.ignore_in_sp_commission=0 and item.disable_in_sp_commission=0 and (si.additional_discount_percentage <> 100 or si.additional_discount_percentage is null) and si.status='Paid' and sii.is_accrual=0 and si.currency=%s and acc.account_currency=%s and si.posting_date >= %s and si.posting_date <= %s and si.docstatus=1 
		
		 """,[self.transaction_currency,self.transaction_currency,self.from_date,self.to_date], as_dict=True)

	def get_exchange_rate(self):
		return frappe.db.sql("""select exchange_rate as rate
			from `tabCurrency Exchange`
			where from_currency= %s and to_currency= %s order by date desc limit 1 """,
			[self.transaction_currency,self.c_currency], as_dict=True)

	def fill_commission(self):
		self.items=None
		
		data=[]
		self.transaction_currency=frappe.db.get_single_value("PAV Healthcare Settings", "transaction_currency")
		self.additional_amount_account=frappe.db.get_single_value("PAV Healthcare Settings", "additional_amount_account")
		self.cost_center=frappe.db.get_single_value("PAV Healthcare Settings", "default_cost_center")
		exchange_rate=self.get_exchange_rate()
		self.exchange_rate=exchange_rate[0].rate
		# frappe.msgprint(transaction_currency)
		commissions = self.get_commissions_list()
		if not commissions:
				frappe.msgprint(_("No commissions"))
		for d in commissions:
			row=self.append('items', {})
			row.transaction_currency=self.transaction_currency
			row.sales_invoice=d.sale
			row.item_code=d.item_code
			row.item_name=d.item_name
			row.qty=d.qty
			row.amount=d.rate
			row.patient=d.patient
			row.patient_name=d.patient_name
			row.customer=d.customer
			row.customer_name=d.customer_name
			# if not d.external:
				
			# if not d.internal:
				
			details=get_item_detail(self.company,d.item_code)
			# frappe.msgprint(frappe.as_json(details))
			row.item_account=d.income_account
			row.item_group=details['item_group']
			row.cost_center=d.cost_center
			# row.project=details['project']
			row.sales_partner_amount=0.0
			row.sales_partner_marketer_amount=0.0

			if d.sales_partner_name:
				row.sales_partner=d.sales_partner_name
				rate=get_item_commission(item=d.item_code,item_group=row.item_group,party=d.sales_partner_name,party_type='Sales Partner')				
				# row.sales_partner_amount= flt(ex *self.exchange_rate)
				row.sales_partner_amount=flt(rate *row.qty)
				
				
				if d.sales_partner_marketer:
					row.sales_partner_marketer=d.sales_partner_marketer
					# if row.sales_invoice=='Rad-20104':
					# 	frappe.throw("{0}-{1}-{2}-{3}".format(d.item_code,row.item_group,))
					rate=get_item_commission(item=d.item_code,item_group=row.item_group,party=d.sales_partner_marketer,party_type='Sales Partner Marketer')
					# row.market_amount=flt(m*self.exchange_rate)
					row.sales_partner_marketer_amount=flt(rate*row.qty)
					
					

			# frappe.msgprint("{0},{1}.{2}".format(row.internal_amount,row.sales_partner_amount,row.market_amount))
			row.total_commission=(row.sales_partner_amount+row.sales_partner_marketer_amount)
			row.remaining_amount=row.amount-row.total_commission
			row.sii_no=d.sii_no
		self.sales_partner_account=frappe.db.get_single_value("PAV Healthcare Settings", "sales_partner_account")
		self.sales_partner_marketer_account=frappe.db.get_single_value("PAV Healthcare Settings", "sales_partner_marketer_account")
		
		# frappe.throw(parties_row)
		self.save()		
		self.reload()

# def get_marketer(dr):
# 	return frappe.db.sql("""select sales_partner_marketer from `tabSales Partner` where partner_type='Doctor'
# 	and name=%s 
# 	""",dr, as_dict=True)

def get_item_commission(item=None,item_group=None, party=None,party_type=None):
	# it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item=%s and party is null and partner_type is null and party_type is null and disabled=0 limit 1""",[item])	
	it_doc=None
	# if not it_doc and item:
	# 	it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and disabled=0 limit 1""",[item])
	# if not it_doc and item_group:
	# 	it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and disabled=0 limit 1""",[item_group])
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