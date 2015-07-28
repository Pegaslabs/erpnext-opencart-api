from __future__ import unicode_literals
from frappe import _, msgprint, throw
from erpnext.accounts.party import get_party_account, get_due_date

import frappe

# from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


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


@frappe.whitelist()
def set_missing_values(self, for_validate=False):
    raise Exception('sales_invoice')
    self.set_pos_fields(for_validate)
    if not self.debit_to:
        self.debit_to = get_party_account(self.company, self.customer, "Customer")
    if not self.due_date:
        self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

    #super(SalesInvoice, self).set_missing_values(for_validate)

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
