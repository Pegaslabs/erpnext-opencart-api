from __future__ import unicode_literals
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, flt
from erpnext.accounts.party import get_party_account, get_due_date

from frappe.model.mapper import get_mapped_doc

import frappe

# import gorilla

from mode_of_payments import is_pos_payment_method
from delivery_note import on_delivery_note_added

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


def validate(doc, method=None):
    db_sales_invoice = frappe.db.get_value('Sales Invoice', {'sales_order': doc.sales_order}, ['name', 'docstatus'], as_dict=True)
    if db_sales_invoice is not None and db_sales_invoice.get('docstatus') != 2:
        frappe.throw('Cannot make new Sales Invoice: Sales Order is already had Sales Invoice %s and its docstatus is not canceled.' % db_sales_invoice.get('name'))


# from erpnext.controllers.selling_controller import SellingController


# @gorilla.patch(sales_invoice)
# class SalesInvoice2():
#     def set_missing_values(self, for_validate=False):
#         frappe.msgprint('set_missing_values from OpencartSalesInvoice777')
#         self.set_pos_fields(for_validate)

#         if not self.debit_to:
#             self.debit_to = get_party_account(self.company, self.customer, "Customer")
#         if not self.due_date:
#             self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

#         super(SalesInvoice, self).set_missing_values(for_validate)


# @gorilla.patch(SalesInvoice)
def set_missing_values(self, for_validate=False):
    # self.set_pos_fields(for_validate)
    if not self.debit_to:
        self.debit_to = get_party_account(self.company, self.customer, "Customer")
    if not self.due_date:
        self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

    super(SalesInvoice, self).set_missing_values(for_validate)


# import types
# setattr(SalesInvoice, set_missing_values.__name__, types.MethodType(set_missing_values, SalesInvoice))
setattr(SalesInvoice, 'set_missing_values', set_missing_values)


@frappe.whitelist()
def resolve_mode_of_payment(payment_method_code, country_territory):
    parent_territory = frappe.db.get_value('Territory', country_territory, 'parent_territory')
    all_mops = frappe.db.get_all('Mode of Payment', fields=['name'], filters={'oc_payment_method_code': payment_method_code})
    for mop in all_mops:
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


def on_submit(self, method=None):
    pass


    # from erpnext.selling.doctype.customer.customer import get_customer_outstanding
    # customer_outstanding = get_customer_outstanding(self.customer, self.company)
    # frappe.msgprint('method=' + str(method))
    # frappe.msgprint('self.customer=%s, self.company=%s' % (self.customer, self.company))
    # frappe.msgprint(str(customer_outstanding))

    # if doc.get('oc_check_totals'):
    #     oc_sub_total = get_rate_from_total_str(doc.get('oc_sub_total') or '')
    #     # oc_shipping_total = get_rate_from_total_str(doc.get('oc_shipping_total') or '')
    #     # oc_tax_total = get_rate_from_total_str(doc.get('oc_tax_total') or '')
    #     oc_total = get_rate_from_total_str(doc.get('oc_total') or '')

    #     if not are_totals_equal(doc.get('total'), oc_sub_total):
    #         frappe.throw('%s: Order\'s Total ($%s) does not equal to Sub Total ($%s) from Opencart site' % (doc.get('name'), str(doc.get('total')), str(oc_sub_total)))
    #     if not are_totals_equal(doc.get('grand_total'), oc_total):
    #         frappe.throw('%s: Order\'s Grand Total ($%s) does not equal to Total ($%s) from Opencart site' % (doc.get('name'), str(doc.get('grand_total')), str(oc_total)))

    # # frappe.db.set(doc, 'oc_status', OC_ORDER_STATUS_PROCESSING)
    # # sync_order_to_opencart(doc)

    # # # update Opencart status
    # # if doc_order.get('status') is None or doc_order.get('status') == 'Draft':
    # # elif doc_order.get('status') == 'Submitted':
    # # elif doc_order.get('status') == 'Stopped':
    # # elif doc_order.get('status') == 'Cancelled':


def on_sales_invoice_added(doc_sales_invoice):
    try:
        if is_pos_payment_method(doc_sales_invoice.oc_pm_code):
            doc_sales_invoice.submit()
    except Exception as ex:
        frappe.msgprint('Sales Invoice "%s" was not submitted.\n%s' % (doc_sales_invoice.get('name'), str(ex)))
    else:
        dn = make_delivery_note(doc_sales_invoice.get('name'))
        dn.insert()
        on_delivery_note_added(dn.get('name'))


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):

    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.base_amount = (flt(source_doc.qty) - flt(source_doc.delivered_qty)) * \
            flt(source_doc.base_rate)
        target_doc.amount = (flt(source_doc.qty) - flt(source_doc.delivered_qty)) * \
            flt(source_doc.rate)
        target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)

    db_sales_order = frappe.db.get_value('Sales Invoice', source_name, 'sales_order')
    db_delivery_note_docstatus = frappe.db.get_value('Delivery Note', {'sales_order': db_sales_order}, 'docstatus')
    if db_delivery_note_docstatus is not None and db_delivery_note_docstatus != 2:
        frappe.throw('Cannot make new Delivery Note: Delivery Note is already created and its docstatus is not canceled.')

    doclist = get_mapped_doc("Sales Invoice", source_name, {
        "Sales Invoice": {
            "doctype": "Delivery Note",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Sales Invoice Item": {
            "doctype": "Delivery Note Item",
            "field_map": {
                "name": "si_detail",
                "parent": "against_sales_invoice",
                "serial_no": "serial_no",
                "sales_order": "against_sales_order",
                "so_detail": "so_detail"
            },
            "postprocess": update_item
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "field_map": {
                "incentives": "incentives"
            },
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return doclist


@frappe.whitelist()
def get_sales_statistic(sales_order):
    delivery_note_no = frappe.db.get_values('Delivery Note', {'sales_order': sales_order}, 'name')
    sales_invoice_no = frappe.db.get_values('Sales Invoice', {'sales_order': sales_order}, 'name')
    packing_slip_no = frappe.db.get_values('Packing Slip', {'sales_order': sales_order}, 'name')
    return {'delivery_note': delivery_note_no, 'sales_invoice': sales_invoice_no, 'packing_slip': packing_slip_no}
