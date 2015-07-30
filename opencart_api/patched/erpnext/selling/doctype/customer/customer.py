from __future__ import unicode_literals
import frappe

from frappe import _, msgprint, throw
from frappe.utils import flt

from erpnext.selling.doctype.customer.customer import get_customer_outstanding, get_credit_limit


def check_credit_limit(customer, company):
    is_credit_ok = True
    customer_outstanding = get_customer_outstanding(customer, company)
    credit_limit = get_credit_limit(customer, company)

    if credit_limit is None:
        msgprint(_("Credit limit is not set for customer {0}.\nPlease adjust credit limit either for customer or customer group or company.").format(customer))
        is_credit_ok = False
    elif credit_limit > 0 and flt(customer_outstanding) > credit_limit:
        msgprint(_("Credit limit has been crossed for customer {0} {1}/{2}").format(customer, customer_outstanding, credit_limit))
        is_credit_ok = False

        # If not authorized person raise exception
        credit_controller = frappe.db.get_value('Accounts Settings', None, 'credit_controller')
        if not credit_controller or credit_controller not in frappe.get_roles():
            throw(_("Please contact to the user who have Sales Master Manager {0} role").format(" / " + credit_controller if credit_controller else ""))

    return is_credit_ok
