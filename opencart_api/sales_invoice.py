from __future__ import unicode_literals
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, flt
from erpnext.accounts.party import get_party_account, get_due_date

from frappe.model.mapper import get_mapped_doc

import frappe

# import gorilla

from mode_of_payments import is_pos_payment_method
from delivery_note import on_delivery_note_added

from erpnext.accounts.doctype.sales_invoice import sales_invoice as erpnext_sales_invoice


@frappe.whitelist()
def resolve_mode_of_payment(payment_method_code, country_territory):
    parent_territory = frappe.db.get_value('Territory', country_territory, 'parent_territory')
    all_mops = frappe.db.get_all('Mode of Payment', fields=['name', 'oc_payment_method_code'])
    for mop in all_mops:
        if mop.get('oc_payment_method_code'):
            for i in mop.get('oc_payment_method_code').split(','):
                if i.strip() == payment_method_code:
                    doc_mop = frappe.get_doc('Mode of Payment', mop.get('name'))
                    for app_territory in doc_mop.get('oc_territories'):
                        if app_territory.get('territory') == 'All Territories':
                            return doc_mop.get('name')
                        elif app_territory.get('territory') == 'Rest Of The World' and parent_territory == 'Rest Of The World':
                            return doc_mop.get('name')
                        elif app_territory.get('territory') == country_territory:
                            return doc_mop.get('name')
    frappe.msgprint('Cannot resolve Mode Of Payment for Opencart payment method code "%s" and Territory "%s".\nPlease setup Mode Of Payment entries.' % (payment_method_code, country_territory))
    return ''


def on_sales_invoice_added(doc_sales_invoice):
    try:
        if is_pos_payment_method(doc_sales_invoice.oc_pm_code):
            doc_sales_invoice.submit()
    except Exception as ex:
        frappe.msgprint('Sales Invoice "%s" was not submitted.\n%s' % (doc_sales_invoice.get('name'), str(ex)))
    else:
        dn = erpnext_sales_invoice.make_delivery_note(doc_sales_invoice.get('name'))
        dn.insert()
        on_delivery_note_added(dn.get('name'))


@frappe.whitelist()
def get_sales_statistic(sales_order):
    back_order_no = frappe.db.get_values('Back Order', {'docstatus': '0', 'customer': frappe.db.get_value('Sales Order', sales_order, 'customer')}, 'name')
    delivery_note_no = frappe.db.get_values('Delivery Note', {'sales_order': sales_order}, 'name')
    sales_invoice_no = frappe.db.get_values('Sales Invoice', {'sales_order': sales_order}, 'name')
    packing_slip_no = frappe.db.get_values('Packing Slip', {'sales_order': sales_order}, 'name')
    return {
        'back_order': back_order_no,
        'delivery_note': delivery_note_no,
        'sales_invoice': sales_invoice_no,
        'packing_slip': packing_slip_no
    }
