from __future__ import unicode_literals
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, flt
from erpnext.accounts.party import get_party_account, get_due_date

import frappe

import gorilla

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

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
    frappe.msgprint('set_missing_values from OpencartSalesInvoice123')
    self.set_pos_fields(for_validate)

    if not self.debit_to:
        self.debit_to = get_party_account(self.company, self.customer, "Customer")
    if not self.due_date:
        self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

    super(SalesInvoice, self).set_missing_values(for_validate)


# import types
# setattr(SalesInvoice, set_missing_values.__name__, types.MethodType(set_missing_values, SalesInvoice))
setattr(SalesInvoice, 'set_missing_values', set_missing_values)


@frappe.whitelist()
def set_pos_fields(self, for_validate=False):
        """Set retail related fields from POS Profiles"""
        if cint(self.is_pos) != 1:
            return

        from erpnext.stock.get_item_details import get_pos_profiles_item_details, get_pos_profiles
        pos = get_pos_profiles(self.company)

        if self.selling_price_list:
            pos.selling_price_list = self.selling_price_list
            pos.currency = self.currency

        if pos:
            if not for_validate and not self.customer:
                self.customer = pos.customer
                # self.set_customer_defaults()

            for fieldname in ('territory', 'naming_series', 'currency', 'taxes_and_charges', 'letter_head', 'tc_name',
                'selling_price_list', 'company', 'select_print_heading', 'cash_bank_account',
                'write_off_account', 'write_off_cost_center'):
                    if (not for_validate) or (for_validate and not self.get(fieldname)):
                        self.set(fieldname, pos.get(fieldname))

            if not for_validate:
                self.update_stock = cint(pos.get("update_stock"))

            # set pos values in items
            for item in self.get("items"):
                if item.get('item_code'):
                    for fname, val in get_pos_profiles_item_details(pos,
                        frappe._dict(item.as_dict()), pos).items():

                        if (not for_validate) or (for_validate and not item.get(fname)):
                            item.set(fname, val)

            # fetch terms
            if self.tc_name and not self.terms:
                self.terms = frappe.db.get_value("Terms and Conditions", self.tc_name, "terms")

            # fetch charges
            if self.taxes_and_charges and not len(self.get("taxes")):
                self.set_taxes()

setattr(SalesInvoice, 'set_pos_fields', set_pos_fields)


@frappe.whitelist()
def resolve_mode_of_payment(payment_method_code, territory=''):
    res_mode_of_payment = ''
    all_mode_of_payments = frappe.get_all('Mode of Payment', fields=['name', 'oc_territory'], filters={'oc_payment_method_code': payment_method_code})
    if len(all_mode_of_payments) == 1:
        res_mode_of_payment = all_mode_of_payments[0].get('name')
    elif len(all_mode_of_payments) > 1:
        for mop in all_mode_of_payments:
            if mop.get('oc_territory') == territory:
                res_mode_of_payment = mop.get('name')
                break
    return res_mode_of_payment


# def check_credit_limit(self):
#     from erpnext.selling.doctype.customer.customer import check_credit_limit
#     check_credit_limit(self.customer, self.company)


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
