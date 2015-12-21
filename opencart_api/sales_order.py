from __future__ import unicode_literals
import frappe
import frappe.utils
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc

from erpnext.selling.doctype.sales_order import sales_order as erpnext_sales_order
from erpnext.accounts.doctype.mode_of_payment.mode_of_payment import resolve_mode_of_payment
from erpnext.accounts.doctype.mode_of_payment.mode_of_payment import is_pos_payment_method

import territories


def update_sales_order_from_back_order(doc_sales_order, doc_back_order):
    back_order_item_map = {i.item_code: i for i in doc_back_order.items}
    sales_order_item_map = {i.item_code: i for i in doc_sales_order.items}
    updated_items = False
    for bo_item_code, bo_doc_item in back_order_item_map.items():
        so_doc_item = sales_order_item_map.get(bo_item_code)
        new_qty = flt(so_doc_item.qty) - flt(bo_doc_item.qty) if (flt(so_doc_item.qty) - flt(bo_doc_item.qty)) > 0 else 0
        if new_qty != so_doc_item.qty:
            so_doc_item.update({
                "qty": new_qty
            })
            so_doc_item.save()
            updated_items = True
    return updated_items


def is_oc_sales_order(doc):
    return bool(doc.get('oc_site'))


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
            target.is_pos = is_pos_payment_method(source.oc_pm_code)
            payment_territory = territories.get_by_country(source.oc_pa_country)
            target.mode_of_payment = resolve_mode_of_payment(source.customer, payment_method_code=source.oc_pm_code, country_territory=payment_territory)

            # payment method
            target.oc_pm_title = source.oc_pm_title
            target.oc_pm_code = source.oc_pm_code
        else:
            target.mode_of_payment = resolve_mode_of_payment(source.customer)

        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.amount = flt(source.amount) - flt(source.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = target.amount / flt(source.rate) if (source.rate and source.billed_amt) else source.qty
        target.income_account = get_income_account(source_parent)
        target.bo_qty = 0.0

    if erpnext_sales_order.has_active_si(source_name):
        frappe.throw('Cannot make new Sales Invoice: Sales Invoice is already created and its docstatus is not canceled.')

    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Sales Invoice",
            "field_map": {
                "name": "sales_order",
            },
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
        if doc.oc_pa_country:
            payment_territory = territories.get_by_country(doc.oc_pa_country)
            mode_of_payment = resolve_mode_of_payment(doc.customer, payment_method_code=doc.oc_pm_code, country_territory=payment_territory)
        else:
            mode_of_payment = resolve_mode_of_payment(doc.customer)

    if mode_of_payment:
        cash_bank_account = frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment, 'parenttype': 'Mode of Payment', 'company': doc.company}, 'default_account')

    if not cash_bank_account:
        cash_bank_account = frappe.db.get_value("Company", doc.company, "default_bank_account") or ''

    return cash_bank_account
