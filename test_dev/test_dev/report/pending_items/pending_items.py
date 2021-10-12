# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = [
		_("Quotation No") + ":Link/Quotation:120",_("Customer ID") + ":Link/Customer:140", _("Customer Name") + "::140",_("Item Code") + ":Link/Item:140", _("Item Name") + "::140",
		_("Qty") + ":Float:80", _("Rate") + ":Currency:120", _("Grand Total") + ":Currency:120",_("Status") + "::100", _("Sales Order") + ":Link/Sales Order:120",
		_("Ordered Qty") + ":Float:80", _("Ordered Rate") + ":Currency:120", _("Ordered Amount") + ":Currency:120", _("Pending Qty") + ":Float:80", _("Pending Amount") + ":Currency:120"
	]
	data = get_data(filters)
	chart = []
	return columns, data, None, chart


def get_conditions(filters={}):
	conditions = " qi.docstatus = 1 "

	if filters.get("company"): 		conditions += " and q.company = %(company)s "
	if filters.get("quotation"): 	conditions += " and q.name = %(quotation)s "
	if filters.get("customer"): 	conditions += " and q.party_name = %(customer)s "
	if filters.get("item_code"): 	conditions += " and qi.item_code = %(item_code)s "
	if filters.get("from_date"): 	conditions += " and q.transaction_date >= %(from_date)s "
	if filters.get("to_date"): 		conditions += " and q.transaction_date <= %(to_date)s "
	if filters.get("sales_order"): 	conditions += " and soi.parent = %(sales_order)s "

	return conditions


def get_data(filters={}):
	condition = get_conditions(filters)

	result = frappe.db.sql("""
		SELECT 
			q.name,
			q.party_name,
			q.customer_name,
			qi.item_code,
			qi.item_name,
			qi.qty,
			qi.rate,
			qi.net_amount,
			IF(ifnull(soi.qty, 0) > 0 , "Ordered", "No Order"),
			soi.parent,
			sum(ifnull(soi.qty,0)) ordered_qty,
			sum(ifnull(soi.rate,0)) ordered_rate,
			sum(ifnull(soi.net_amount,0)) ordered_amount,
			qi.qty - ifnull(soi.qty, 0) as pending_qty,
			qi.net_amount - ifnull(soi.net_amount, 0) as pending_amount
		FROM
			`tabQuotation Item` qi
				LEFT JOIN
			`tabQuotation` q ON qi.parent = q.name
				LEFT JOIN
			`tabSales Order Item` soi ON qi.parent = soi.prevdoc_docname
					AND qi.item_code = soi.item_code and soi.docstatus = 1
			WHERE
				%s
			GROUP BY 
				qi.parent, qi.item_code
			ORDER BY
				q.transaction_date DESC

	""" % (condition),
		{
			"company":	filters.get("company"),
			"quotation":filters.get("quotation"),
			"customer":	filters.get("customer"),
			"item_code":filters.get("item_code"),
			"from_date":filters.get("from_date"),
			"to_date":	filters.get("to_date"),
			"sales_order":filters.get("sales_order")
		})

	return result