from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and
from frappe import _
from frappe.model.mapper import get_mapped_doc

# from erpnext.controllers.selling_controller import SellingController

import territories
import sales_invoice
from sales_invoice import resolve_mode_of_payment
import mode_of_payments


def is_oc_sales_order(doc):
    return bool(doc.get('oc_site'))


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        if source.po_no:
            if target.po_no:
                target_po_no = target.po_no.split(", ")
                target_po_no.append(source.po_no)
                target.po_no = ", ".join(list(set(target_po_no))) if len(target_po_no) > 1 else target_po_no[0]
            else:
                target.po_no = source.po_no

        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
        target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
        target.qty = flt(source.qty) - flt(source.delivered_qty)

    target_doc = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Delivery Note",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Sales Order Item": {
            "doctype": "Delivery Note Item",
            "field_map": {
                "rate": "rate",
                "name": "so_detail",
                "parent": "against_sales_order",
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.delivered_qty < doc.qty
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return target_doc


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    def postprocess(source, target):
        set_missing_values(source, target)
        #  Get the advance paid Journal Entries in Sales Invoice Advance
        target.get_advances()

    def set_missing_values(source, target):
        target.cash_bank_account = get_cash_bank_account(source, mode_of_payment=target.mode_of_payment)
        target.is_pos = 0

        if is_oc_sales_order(source):
            target.is_pos = mode_of_payments.is_pos_payment_method(source.oc_pm_code)
            payment_territory = territories.get_by_country(source.oc_pa_country)
            target.mode_of_payment = resolve_mode_of_payment(source.oc_pm_code, payment_territory)

            # payment method
            target.oc_pm_title = source.oc_pm_title
            target.oc_pm_code = source.oc_pm_code

        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.amount = flt(source.amount) - flt(source.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = target.amount / flt(source.rate) if (source.rate and source.billed_amt) else source.qty
        target.income_account = get_income_account(source_parent)

    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Sales Invoice",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Sales Order Item": {
            "doctype": "Sales Invoice Item",
            "field_map": {
                "name": "so_detail",
                "parent": "sales_order",
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.base_amount == 0 or doc.billed_amt < doc.amount
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, postprocess)

    return doclist


def get_income_account(doc):
    income_account = frappe.db.get_value("Warehouse", doc.warehouse, "default_income_account") or ''
    if not income_account:
        income_account = frappe.db.get_value("Company", doc.company, "default_income_account") or ''
    return income_account


def get_cash_bank_account(doc, mode_of_payment=None):
    cash_bank_account = ''
    if mode_of_payment is None:
        payment_territory = territories.get_by_country(doc.oc_pa_country)
        mode_of_payment = resolve_mode_of_payment(doc.oc_pm_code, payment_territory)

    if mode_of_payment:
        cash_bank_account = frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment, 'parenttype': 'Mode of Payment', 'company': doc.company}, 'default_account')

    if not cash_bank_account:
        cash_bank_account = frappe.db.get_value("Company", doc.company, "default_bank_account") or ''

    return cash_bank_account
