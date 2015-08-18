from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and
from frappe import _
from frappe.model.mapper import get_mapped_doc, map_doc

# from erpnext.controllers.selling_controller import SellingController

import territories
import sales_invoice
from sales_invoice import resolve_mode_of_payment
import mode_of_payments


def validate(doc, method=None):
    pass


def on_update(doc, method=None):
    if doc.back_order_items:
        back_orders = frappe.db.get_all('Back Order', filters={'sales_order': doc.name, 'docstatus': 0})
        if len(back_orders) > 1:
            frappe.throw('Only one Back Order can be linked with Sales Order')
        elif len(back_orders) == 1:
            new_doc_back_order = make_back_order(doc.name)
            if new_doc_back_order.items:
                doc_back_order = frappe.get_doc('Back Order', back_orders[0].get('name'))
                doc_back_order.items = new_doc_back_order.items
                doc_back_order.save()
                update_sales_order_from_back_order(doc, new_doc_back_order)
                frappe.clear_cache()
        else:
            doc_back_order = make_back_order(doc.name)
            if doc_back_order.items:
                doc_back_order.save()
                frappe.msgprint('Back Order %s is created and linked to this Sales Order' % doc_back_order.name)
                update_sales_order_from_back_order(doc, doc_back_order)

    # frappe.db.get_value("Stock Settings", None, "allow_negative_stock")
    # def update_current_stock(self):
    #     if self.get("_action") and self._action != "update_after_submit":
    #         for d in self.get('items'):
    #             d.actual_qty = frappe.db.get_value("Bin", {"item_code": d.item_code,
    #                 "warehouse": d.warehouse}, "actual_qty")

    #         for d in self.get('packed_items'):
    #             bin_qty = frappe.db.get_value("Bin", {"item_code": d.item_code,
    #                 "warehouse": d.warehouse}, ["actual_qty", "projected_qty"], as_dict=True)
    #             if bin_qty:
    #                 d.actual_qty = flt(bin_qty.actual_qty)
    #                 d.projected_qty = flt(bin_qty.projected_qty)


# def update_back_order(doc_back_order, doc_sales_order):
#     doc_back_order.items = []
#     for source_item in doc_sales_order.items:
#         target_item = frappe.get_doc({'doctype': 'Back Order Item'})
#         if flt(source_item.qty) - flt(source_item.actual_qty) > 0:
#             map_doc(source_item, target_item, {}, None)
#             target_item.qty = flt(source_item.qty) - flt(source_item.actual_qty)
#             target_item.base_amount = flt(target_item.qty) * flt(source_item.base_rate)
#             target_item.amount = flt(target_item.qty) * flt(source_item.rate)
#             frappe.msgprint('===' + str(target_item.qty))
#             doc_back_order.items.append(target_item)


def update_sales_order_from_back_order(doc_sales_order, doc_back_order):
    back_order_item_map = {i.item_code: i for i in doc_back_order.items}
    sales_order_item_map = {i.item_code: i for i in doc_sales_order.items}
    for bo_item_code, bo_doc_item in back_order_item_map.items():
        so_doc_item = sales_order_item_map.get(bo_item_code)
        so_doc_item.update({
            "qty": flt(so_doc_item.qty) - flt(bo_doc_item.qty),
        })
        so_doc_item.save()


@frappe.whitelist()
def make_back_order(source_name, target_doc=None):
    def postprocess(source, target):
        target.items = [item for item in target.items if item.qty > 0]

    def update_item(obj, target, source_parent):
        target.qty = flt(obj.qty) - flt(obj.projected_qty) if flt(obj.qty) > flt(obj.projected_qty) else 0
        target.base_amount = flt(target.qty) * flt(obj.base_rate)
        target.amount = flt(target.qty) * flt(obj.rate)

    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Back Order",
            "field_map": {
                "name": "sales_order",
            }
        },
        "Sales Order Item": {
            "doctype": "Back Order Item",
            "field_map": {
                "parent": "prevdoc_docname"
            },
            "postprocess": update_item
        }
    }, target_doc, postprocess)

    return doclist


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

    db_delivery_docstatus = frappe.db.get_value('Delivery Note', {'sales_order': source_name}, 'docstatus')
    if db_delivery_docstatus is not None and db_delivery_docstatus != 2:
        frappe.throw('Cannot make new Delivery Note: Delivery Note is already created and its docstatus is not canceled.')

    target_doc = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Delivery Note",
            "field_map": {
                "name": "sales_order",
            },
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

    db_sales_invoice_docstatus = frappe.db.get_value('Sales Invoice', {'sales_order': source_name}, 'docstatus')
    if db_sales_invoice_docstatus is not None and db_sales_invoice_docstatus != 2:
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
        payment_territory = territories.get_by_country(doc.oc_pa_country)
        mode_of_payment = resolve_mode_of_payment(doc.oc_pm_code, payment_territory)

    if mode_of_payment:
        cash_bank_account = frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment, 'parenttype': 'Mode of Payment', 'company': doc.company}, 'default_account')

    if not cash_bank_account:
        cash_bank_account = frappe.db.get_value("Company", doc.company, "default_bank_account") or ''

    return cash_bank_account


@frappe.whitelist()
def get_back_order_list(sales_order):
    return frappe.db.get_values('Back Order', {'docstatus': '0', 'customer': frappe.db.get_value('Sales Order', sales_order, 'customer')}, 'name', as_dict=True)


@frappe.whitelist()
def load_items_from_back_order(sales_order, back_order, submit_back_order):
    doc_back_order = frappe.get_doc('Back Order', back_order)
    doc_sales_order = frappe.get_doc('Sales Order', sales_order)

    back_order_item_map = {i.item_code: i for i in doc_back_order.items}
    sales_order_item_map = {i.item_code: i for i in doc_sales_order.items}
    for bo_item_code, bo_doc_item in back_order_item_map.items():
        so_doc_item = sales_order_item_map.get(bo_item_code)
        if so_doc_item:  # update Sales Order Item
            so_doc_item.update({
                "qty": flt(so_doc_item.qty) + flt(bo_doc_item.qty),
            })
        else:  # add new Sales Order Item from Back Order Item
            doc_sales_order.append("items", {
                "item_code": bo_doc_item.item_code,
                "qty": flt(bo_doc_item.qty),
            })
    doc_sales_order.update({'back_order_items': 0})
    doc_sales_order.save()

    if submit_back_order:
        doc_back_order.submit()
