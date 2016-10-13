from __future__ import unicode_literals
import frappe
import frappe.utils
from frappe.utils import cstr, flt

OC_ORDER_TYPE_LUSTCOBOX = "lustcobox"


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


def is_paypal_sales_order(sales_order):
    return cstr(frappe.db.get_value("Sales Order", sales_order, "oc_pm_code")).strip() in ("pp_express", "pp_pro")


def is_paypal_sales_order_doc(sales_order_doc):
    return cstr(sales_order_doc.oc_pm_code).strip() in ("pp_express", "pp_pro")


def is_stripe_sales_order(sales_order):
    return cstr(frappe.db.get_value("Sales Order", sales_order, "oc_pm_code")).strip() == "stripe"


def is_stripe_sales_order_doc(sales_order_doc):
    return cstr(sales_order_doc.oc_pm_code).strip() == "stripe"


def is_converge_sales_order(sales_order):
    return cstr(frappe.db.get_value("Sales Order", sales_order, "oc_pm_code")).strip() == "virtualmerchant"


def is_converge_sales_order_doc(sales_order_doc):
    return cstr(sales_order_doc.oc_pm_code).strip() == "virtualmerchant"


def is_oc_sales_order(doc):
    return bool(doc.get('oc_site'))


def is_oc_lustcobox_order_doc(sales_order_doc):
    return is_oc_lustcobox_order_type(sales_order_doc.oc_order_type)


def is_oc_lustcobox_order(sales_order):
    return is_oc_lustcobox_order_type(frappe.db.get_value("Sales Order", sales_order, "oc_order_type"))


def is_oc_lustcobox_order_type(oc_order_type):
    return oc_order_type == OC_ORDER_TYPE_LUSTCOBOX
