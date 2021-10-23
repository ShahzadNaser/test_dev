
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, add_months, format_date, get_last_day,format_date
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns, query = get_columns(filters)
	data = get_data(filters, query)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"label": _("Item"),
			"options":"Item",
			"fieldname": "name",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Item Name"),
			"options":"Item",
			"fieldname": "item_name",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Item Group"),
			"options":"Item Group",
			"fieldname": "item_group",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Data",
			"width": 120
		}]

	temp_columns, query = get_period_date_ranges(filters)
	columns = columns + temp_columns
	return columns, query

def get_period_date_ranges(filters):
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	r = relativedelta(to_date,from_date)
	months_difference = (r.years * 12) + r.months + 1
	columns = []
	query = ""

	for i in range(months_difference):
		date1 = get_last_day(add_months(from_date, i))
		date2 = format_date(date1,"MMM-YYYY")

		str1 = "sum(case when sle.posting_date <= '{0}' then actual_qty else 0 end)".format(date1)
		str2 = "ABS(sum(case when DATE_FORMAT(sle.posting_date,'%%b-%%Y') = '{0}' and sle.voucher_type = 'Sales Invoice' then actual_qty else 0 end))".format(date2)

		query += " , {0} '{2} Balance', {1} '{2} Sale', ABS(({1}/{0})*100) '{2} Selling'".format(str1, str2 , date2)

		columns.append({"label": _("{0} Balance".format(date1)), "fieldtype": "Float","width": 80})
		columns.append({"label": _("{0} Sale".format(date2)), "fieldtype": "Float","width": 80})
		columns.append({"label": _("{0} Sale %".format(date2)), "fieldtype": "Percent","width": 80})
		
	return columns, query
def get_conditions(filters={}):
	conditions = " sle.company = %(company)s "

	if filters.get("item_code"): 	conditions += " and sle.item_code = %(item_code)s "
	if filters.get("warehouse"): 	conditions += " and sle.warehouse >= %(warehouse)s "
	if filters.get("to_date"): 		conditions += " and sle.posting_date <= %(to_date)s "
	
	return conditions


def get_data(filters, query):
	condition = get_conditions(filters)

	result = frappe.db.sql("""
		SELECT 
			i.item_code,
			i.item_name,
			i.item_group
			%s
		FROM
			`tabItem` i
		LEFT JOIN
			`tabStock Ledger Entry` sle ON i.item_code = sle.item_code
		WHERE
			%s
		GROUP BY i.item_code

	""" % (query, condition),
		{
			"company":	filters.get("company"),
			"item_code":filters.get("item_code"),
			"warehouse":filters.get("warehouse"),
			"to_date":	filters.get("to_date")
		}, debug=True)

	return result




