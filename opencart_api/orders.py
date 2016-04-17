from __future__ import unicode_literals
from datetime import datetime
import re
import copy

import frappe
from frappe.utils import add_days, nowdate, getdate, cstr, flt, cint
from erpnext.accounts.doctype.sales_invoice import sales_invoice as erpnext_sales_invoice
from erpnext.selling.doctype.sales_order import sales_order as erpnext_sales_order
from erpnext.stock.doctype.delivery_note.delivery_note import make_packing_slip
from erpnext.selling.doctype.customer.customer import check_credit_limit, add_existed_credit_card
from erpnext.accounts.doctype.mode_of_payment.mode_of_payment import is_pos_payment_method
from erpnext.accounts.utils import get_fiscal_year

from utils import sync_info
from decorators import sync_to_opencart
import addresses
import oc_api
import oc_site
import customers
import oc_stores
import items
import territories
import sales_taxes_and_charges_template
import sales_order


OC_ORDER_STATUS_AWAITING_FULFILLMENT = 'Awaiting Fulfillment'
OC_ORDER_STATUS_PROCESSING = 'Processing'
OC_ORDER_STATUS_SHIPPED = 'Shipped'
OC_ORDER_STATUS_COMPLETE = 'Complete'
OC_ORDER_STATUS_CANCELED = 'Canceled'


OC_CURRENCY_REGEX = re.compile("([A-Z]{3})")
OC_TOTAL_REGEX = re.compile("([-+]?[\d,.]+)")

TOTALS_PRECISION = 0.02


def get_currency_from_total_str(total_str):
    '''Getting currency from the strings like "$ 123.456$ CAD"'''
    currency_code = ''
    s = OC_CURRENCY_REGEX.search(total_str)
    if s:
        currency_code = s.group(1)
    return currency_code


def get_rate_from_total_str(total_str):
    '''Getting rate from the strings like "$ 123.456$ CAD"'''
    price = 0.0
    s = OC_TOTAL_REGEX.search(total_str)
    if s:
        price = float(s.group(1).replace(',', ''))
    return price


def are_totals_equal(total1, total2):
    if abs(total1 - total2) < TOTALS_PRECISION:
        return True
    return False


def before_save(doc, method=None):
    sync_order_to_opencart(doc)


def validate(doc, method=None):
    if doc.oc_cc_token_id and not frappe.db.get("Credit Card", {"card_token": doc.oc_cc_token_id}):
        frappe.throw("Cannot find Credit Card with token id {}, Sales Order {}, OC Order ID {}".format(doc.oc_cc_token_id, doc.name, doc.oc_order_id))


def on_submit(doc, method=None):
    if sales_order.is_oc_sales_order(doc):
        if sales_order.is_oc_lustcobox_order_doc(doc):
            check_oc_sales_order_totals(doc)

            recurring_profile = frappe.db.get_value("Recurring Profile", {"sales_order": doc.name}, "name")
            if not recurring_profile:
                add_lustcobox_order_part(doc, oc_order=None)
                recurring_profile = frappe.db.get_value("Recurring Profile", {"sales_order": doc.name}, "name")
            if sales_order.is_converge_sales_order_doc(doc) and not doc.oc_cc_token_id:
                frappe.throw("You cannot submit Sales Order {} due to CC Token Id is not set".format(doc.name))
            if (sales_order.is_stripe_sales_order_doc(doc) or sales_order.is_paypal_sales_order_doc(doc))and not doc.oc_cheque_no and not doc.oc_cheque_date:
                frappe.throw("You cannot submit Sales Order {} due to either Cheque No or Cheque Date is not set".format(doc.name))

            recurring_profile_doc = frappe.get_doc("Recurring Profile", recurring_profile)
            recurring_profile_doc.activate(send_email_notifications=doc.oc_send_welcome_email)

            is_stripe = sales_order.is_stripe_sales_order_doc(doc)
            is_paypal = sales_order.is_paypal_sales_order_doc(doc)
            si = sales_order.make_sales_invoice(doc.name, is_recurring=True)
            si.update({
                "reference_type": "Recurring Profile",
                "reference_name": recurring_profile_doc.name,
                "posting_date": doc.transaction_date
            })
            si.insert()
            si.submit()

            from erpnext.accounts.doctype.journal_entry.journal_entry import get_cc_payment_entry_against_invoice, get_payment_entry_against_invoice, add_converge_transaction
            if is_stripe or is_paypal:
                je = frappe.get_doc(get_payment_entry_against_invoice(si.doctype, si.name, is_recurring=True))
                cheque_date = doc.oc_cheque_date
                if cheque_date:
                    cheque_date = getdate(cheque_date)
                je.cheque_no = doc.oc_cheque_no
                je.cheque_date = cheque_date
            else:
                je = frappe.get_doc(get_cc_payment_entry_against_invoice(si.doctype, si.name, is_recurring=True))
            je.posting_date = doc.transaction_date
            je.insert()
            frappe.db.set_value("Recurring Profile", recurring_profile, "current_sales_invoice", si.name)

            if not is_stripe and not is_paypal:
                tr = add_converge_transaction(je.name, si, transaction_args=recurring_profile_doc.as_dict(), transaction_id=recurring_profile_doc.initial_transaction_id)
                tr.submit()

            je.submit()

            if recurring_profile_doc.have_first_box:
                dn = erpnext_sales_invoice.make_delivery_note(si.name)
                dn.update({
                    "reference_type": "Recurring Profile",
                    "reference_name": recurring_profile_doc.name,
                    "posting_date": doc.transaction_date
                })
                dn.insert(ignore_permissions=True)

                ps = make_packing_slip(dn.name)
                ps.update({
                    "reference_type": "Recurring Profile",
                    "reference_name": recurring_profile_doc.name
                })
                ps.get_items()
                ps.insert(ignore_permissions=True)
                ps.receive_all_items()
                ps.oc_tracking_number = "Box was given on hands"

                ps.save()
                ps.start_picking()
                ps.stop_picking()

                frappe.get_doc("Packing Slip", ps.name).submit()
                frappe.get_doc("Delivery Note", dn.name).submit()
            else:
                dn = erpnext_sales_invoice.make_delivery_note(si.name)
                dn.update({
                    "reference_type": "Recurring Profile",
                    "reference_name": recurring_profile_doc.name,
                    "posting_date": doc.transaction_date
                })
                dn.insert(ignore_permissions=True)

                ps = make_packing_slip(dn.name)
                ps.update({
                    "reference_type": "Recurring Profile",
                    "reference_name": recurring_profile_doc.name
                })
                ps.get_items()
                ps.insert(ignore_permissions=True)

        elif not doc.get('oc_is_auto_processing'):
            check_oc_sales_order_totals(doc)
            if is_pos_payment_method(doc.get('oc_pm_code')):
                # submitting orders manually
                # create sales invoice
                si = sales_order.make_sales_invoice(doc.name)
                si.insert()
                frappe.msgprint('Sales Invoice %s was created automatically' % si.name)

            # create delivery note
            dn = erpnext_sales_order.make_delivery_note(doc.name)
            dn.insert()
            frappe.msgprint('Delivery Note %s was created automatically' % dn.name)

            # create packing slip
            ps = make_packing_slip(dn.name)
            ps.get_items()
            ps.insert()
            frappe.msgprint('Packing Slip %s was created automatically' % ps.name)

    else:
        # create delivery note
        dn = erpnext_sales_order.make_delivery_note(doc.name)
        dn.insert()
        frappe.msgprint('Delivery Note %s was created automatically' % dn.name)

        # create packing slip
        ps = make_packing_slip(dn.name)
        ps.get_items()
        ps.insert()
        frappe.msgprint('Packing Slip %s was created automatically' % ps.name)

    # # update Opencart status
    # if doc_order.get('status') is None or doc_order.get('status') == 'Draft':
    # elif doc_order.get('status') == 'Submitted':
    # elif doc_order.get('status') == 'Stopped':
    # elif doc_order.get('status') == 'Cancelled':


def on_cancel(doc, method=None):
    sync_order_status_to_opencart(doc, new_order_status=OC_ORDER_STATUS_CANCELED)


@sync_to_opencart
def on_trash(doc, method=None):
    site_name = doc.get('oc_site')
    oc_order_id = doc.get('oc_order_id')
    success, resp = oc_api.get(site_name).delete_order(oc_order_id)
    if success:
        frappe.msgprint('Order was deleted successfully on Opencart site')
    else:
        frappe.msgprint('Order is not deleted on Opencart site. Error: %s' % resp.get('error', 'Unknown'))


def check_oc_sales_order_totals(doc):
    if sales_order.is_oc_sales_order(doc):
        if doc.get('oc_check_totals'):
            oc_sub_total = get_rate_from_total_str(doc.get('oc_sub_total') or '')
            # oc_shipping_total = get_rate_from_total_str(doc.get('oc_shipping_total') or '')
            # oc_tax_total = get_rate_from_total_str(doc.get('oc_tax_total') or '')
            oc_total = get_rate_from_total_str(doc.get('oc_total') or '')

            if not are_totals_equal(doc.get('total'), oc_sub_total):
                frappe.throw('%s: Order\'s Total ($%s) does not equal to Sub Total ($%s) from Opencart site' % (doc.name, str(doc.get('total')), str(oc_sub_total)))
            if not are_totals_equal(doc.get('grand_total'), oc_total):
                frappe.throw('%s: Order\'s Grand Total ($%s) does not equal to Total ($%s) from Opencart site' % (doc.name, str(doc.get('grand_total')), str(oc_total)))


@sync_to_opencart
def sync_order_status_to_opencart(doc_order, new_order_status=None, new_order_status_id=None):
    ret = False
    site_name = doc_order.get('oc_site')
    oc_order_id = doc_order.get('oc_order_id')
    get_order_success, oc_order = oc_api.get(site_name).get_order_json(oc_order_id)

    if new_order_status is None:
        new_order_status = doc_order.get('oc_status')
    if new_order_status_id is None:
        new_order_status_id = oc_site.get_order_status_id(site_name, new_order_status)
    if oc_order_id and get_order_success and oc_order_id == oc_order.get('order_id'):
        # update existed order on Opencart site
        data = {'status': new_order_status_id}
        success, resp = oc_api.get(site_name).update_order(oc_order_id, data)
        if success:
            frappe.db.set_value('Sales Order', doc_order.get('name'), 'oc_status', new_order_status)
            ret = True
            frappe.msgprint('Order status "%s" is updated successfully on Opencart site' % new_order_status)
        else:
            frappe.msgprint('Order status "%s" is not updated on Opencart site.\nError: %s' % (new_order_status, resp.get('error', 'Unknown')))
    return ret


@sync_to_opencart
def sync_order_to_opencart(doc_order):
    if sales_order.is_oc_lustcobox_order_doc(doc_order):
        return

    site_name = doc_order.get('oc_site')
    # validating customer
    customer_name = doc_order.get('customer')
    doc_customer = frappe.get_doc('Customer', customer_name)
    oc_customer_id = doc_customer.get('oc_customer_id')
    if not oc_customer_id:
        frappe.throw('To sync Order to Opencart Site, Customer "%s" should be existed on Opencart Site' % cstr(customer_name))

    if oc_customer_id == '0':
        # we do not sync orders of guest customers to Opencart site
        return

    get_customer_success, oc_customer = oc_api.get(site_name).get_customer(oc_customer_id)
    if not get_customer_success:
        frappe.throw('Could not get Customer "%s" from Opencart Site. Error: Unknown' % cstr(customer_name))

    # validating customer group
    doc_customer_group = customers.get_customer_group(site_name, oc_customer_id, doc_customer)
    oc_customer_group_id = doc_customer_group.get('oc_customer_group_id')
    if not oc_customer_group_id:
        frappe.throw('To sync Order to Opencart Site, Customer Group "%s" should be existed on Opencart Site' % cstr(doc_customer_group.get('name')))
    get_customer_group_success, oc_customer_group = oc_api.get(site_name).get_customer_group(oc_customer_group_id)
    if not get_customer_group_success:
        frappe.throw('Could not get Customer Group "%s" from Opencart Site. Error: Unknown' % cstr(doc_customer_group.get('name')))

####################
    # oc_order_id = doc_order.get('oc_order_id')
    # get_order_success, oc_order = oc_api.get(site_name).get_order_json(oc_order_id)

    # valid_order_group_names = [order_group.get('name') for order_group in order_groups.get_all_by_oc_site(site_name) if order_group.get('oc_order_group_id')]
    # if order_group_name not in valid_order_group_names:
    #     frappe.throw('To sync Order to Opencart Site, Order Group must be one of the following:\n%s' % cstr(', '.join(valid_order_group_names)))

    data = {
        # 'store_id': '0',
        'customer': {
            'customer_id': doc_customer.get('oc_customer_id'),
            'customer_group_id': oc_customer_group_id,
            'firstname': doc_customer.get('oc_firstname'),
            'lastname': doc_customer.get('oc_lastname'),
            'telephone': doc_customer.get('oc_telephone'),
            'fax': doc_customer.get('oc_fax'),
            'email': doc_customer.get('oc_email'),
            'custom_field': ''
        },
        'payment_address': {
            'firstname': doc_customer.get('oc_firstname'),
            'lastname': doc_customer.get('oc_lastname')
            # 'company': 'company',
            # 'company_id': 'company',
            # 'tax_id': '1',
            # 'address_1': 'Test street 88',
            # 'address_2': 'test',
            # 'postcode': '1111',
            # 'city': 'Berlin',
            # 'zone_id': '1433',
            # 'zone': 'Budapest',
            # 'zone_code': 'BU',
            # 'country_id': '97',
            # 'country': 'Hungary'
        },
        'payment_method': {
            'title': '',
            'code': ''
        },
        'shipping_address': {
            'firstname': doc_customer.get('oc_firstname'),
            'lastname': doc_customer.get('oc_lastname')
            # 'company': 'company',
            # 'address_1': 'Kos',
            # 'address_2': 'test',
            # 'postcode': '1111',
            # 'city': 'Budapest',
            # 'zone_id': '1433',
            # 'zone': 'Budapest',
            # 'zone_code': 'BU',
            # 'country_id': '97',
            # 'country': 'Hungary'
        },
        'shipping_method': {
            # 'title': 'Flat Shipping Rate',
            # 'code': 'flat.flat'
        },
        'comment': doc_customer.get('oc_comment'),
        # 'order_status_id': '2',
        # 'order_status': 'Processing',
        # 'affiliate_id': '',
        # 'commission': '',
        # 'marketing_id': '',
        # 'tracking': '',
        # 'products': [
        #     {
        #         'product_id': '46',
        #         'quantity': '3',
        #         'price': '10',
        #         'total': '10',
        #         'name': 'Sony VAIO',
        #         'model': 'Product 19',
        #         'tax_class_id': '10',
        #         'reward': '0',
        #         'subtract': '0',
        #         'download': '',
        #         'option': [
        #             {
        #                 'product_option_id': 'product_option_id',
        #                 'product_option_value_id': 'product_option_value_id',
        #                 'option_id': 'option_id',
        #                 'option_value_id': 'option_value_id',
        #                 'name': 'name',
        #                 'value': 'value',
        #                 'type': 'type'
        #             }
        #         ]
        #     }
        # ],
        # 'totals': [
        #     {
        #         'code': 'coupon',
        #         'title': 'my coupon',
        #         'value': '10$',
        #         'sort_order': '1'
        #     },
        #     {
        #         'code': 'discount',
        #         'title': 'my discount',
        #         'value': '10$',
        #         'sort_order': '2'
        #     }
        # ]
    }

    # products
    products = []
    for doc_sales_order_item in doc_order.items:
        doc_oc_product = items.get_opencart_product(site_name, doc_sales_order_item.get('item_code'))
        if not doc_oc_product:
            frappe.throw('Could not found "%s %s" Item related to "%s" Opencart Site' % (doc_sales_order_item.get('item_code'),
                                                                                         doc_sales_order_item.get('item_name'),
                                                                                         site_name))
        doc_item = frappe.get_doc('Item', doc_sales_order_item.get('item_code'))
        products.append({
            'product_id': doc_oc_product.get('oc_product_id'),
            'quantity': doc_sales_order_item.get('qty'),
            'price': doc_sales_order_item.get('rate'),
            'total': doc_sales_order_item.get('amount'),
            'name': doc_item.get('item_name'),
            'model': doc_oc_product.get('oc_model'),
            'sku': doc_oc_product.get('oc_sku')
            # 'tax_class_id': '10',
            # 'reward': '0',
            # 'subtract': '0',
            # 'download': '',
            # 'option': [
            #     {
            #         'product_option_id': 'product_option_id',
            #         'product_option_value_id': 'product_option_value_id',
            #         'option_id': 'option_id',
            #         'option_value_id': 'option_value_id',
            #         'name': 'name',
            #         'value': 'value',
            #         'type': 'type'
            #     }
            # ]
        })
    if products:
        data['products'] = products

    oc_order_id = doc_order.get('oc_order_id')
    get_order_success, oc_order = oc_api.get(site_name).get_order_json(oc_order_id)

    # updating or creating order
    order_status_id = oc_site.get_order_status_id(site_name, doc_order.get('oc_status'))
    if oc_order_id and get_order_success and oc_order_id == oc_order.get('order_id'):
        # update existed order on Opencart site
        data = {'status': order_status_id}
        success, resp = oc_api.get(site_name).update_order(oc_order_id, data)
        if success:
            frappe.msgprint('Order is updated successfully on Opencart site')
            doc_order.update({'oc_last_sync_to': datetime.now()})
        else:
            frappe.msgprint('Order is not updated on Opencart site.\nError: %s' % resp.get('error', 'Unknown'))
    else:
        # disabled for now creating new Sales Orders from ERPNext
        return
        # add new order on Opencart site
        success, resp = oc_api.get(site_name).create_order(data)
        if success:
            oc_order_id = resp.get('data', {}).get('id', '')
            doc_order.update({
                'oc_order_id': oc_order_id,
                'oc_last_sync_to': datetime.now()
            })

            # update existed order on Opencart site
            data = {'status': order_status_id}
            success, resp = oc_api.get(site_name).update_order(oc_order_id, data)
            frappe.msgprint('Order is created successfully on Opencart site')
        else:
            frappe.msgprint('Order is not created on Opencart site.\nError: %s' % resp.get('error', 'Unknown'))


def get_order(site_name, oc_order_id):
    db_order = frappe.db.get('Sales Order', {'oc_site': site_name, 'oc_order_id': oc_order_id})
    if db_order:
        return frappe.get_doc('Sales Order', db_order.get('name'))


def update_totals(doc_order, oc_order, tax_rate_names=[]):
    sub_total = ''
    bundle_discount_total = ''
    shipping_total = ''
    tax_rate_name = ''
    tax_total = ''
    total = ''
    for t in oc_order.get('totals', []):
        if t.get('title') == 'Sub-Total':
            sub_total = t.get('text')
        elif t.get('title') in ['Shipping', 'Flat Shipping Rate']:
            shipping_total = t.get('text')
        elif t.get('title') == 'Total':
            total = t.get('text')
        elif t.get('title') in tax_rate_names or t.get('title') == 'VAT':
            tax_rate_name = t.get('title')
            tax_total = t.get('text')
        elif t.get('title') == 'Bundle Discount':
            bundle_discount_total = t.get('text')
        else:
            frappe.msgprint('Unknown total entity "%s" for order %s' % (t.get('title'), oc_order.get('order_id')))

    doc_order.update({
        'oc_sub_total': sub_total,
        'oc_bundle_discount_total': bundle_discount_total,
        'oc_shipping_total': shipping_total,
        'oc_tax_rate_name': tax_rate_name,
        'oc_tax_total': tax_total,
        'oc_total': total
    })
    if bundle_discount_total:
        doc_order.update({
            'discount_amount': abs(get_rate_from_total_str(bundle_discount_total)),
            'apply_discount_on': 'Net Total',
        })


def on_lustcobox_order_added(doc_sales_order, oc_order):
    doc_sales_order.submit()


def add_lustcobox_order_part(doc_sales_order, oc_order=None):
    is_later_add = False
    if oc_order is None:
        is_later_add = True
    if not oc_order:
        get_order_success, oc_order = oc_api.get(doc_sales_order.oc_site).get_order_json(doc_sales_order.oc_order_id)

    lustcobox = oc_order.get(sales_order.OC_ORDER_TYPE_LUSTCOBOX, {})
    lustcobox.update({
        "cc_token": doc_sales_order.oc_cc_token_id,
        "conv_tr_id": doc_sales_order.oc_initial_transaction_id,
        "have_first_box": doc_sales_order.oc_have_first_box
    })
    # if not oc_order.get(sales_order.OC_ORDER_TYPE_LUSTCOBOX):
    #     frappe.throw("Section {} is missed in Sales Order".format(sales_order.OC_ORDER_TYPE_LUSTCOBOX))
    if not is_later_add and not oc_order.get(sales_order.OC_ORDER_TYPE_LUSTCOBOX, {}).get("conv_tr_id"):
        frappe.throw("Lustcobox Sales Orders should have initial transaction id")

    from erpnext.selling.doctype.recurring_profile.recurring_profile import make_recurring_profile
    recurring_profile_doc = make_recurring_profile(doc_sales_order)

    doc_billing_address = addresses.get_from_oc_order(doc_sales_order.oc_site, doc_sales_order.customer, oc_order, address_type='Billing')
    oc_order_copy = copy.deepcopy(oc_order)
    for k, v in lustcobox.items():
        if k.startswith("shipping_"):
            oc_order_copy.update({k: v})
    doc_shipping_address = addresses.get_from_oc_order(doc_sales_order.oc_site, doc_sales_order.customer, oc_order_copy, address_type='Shipping')
    recurring_profile_doc.update({
        "cc_token_id": lustcobox.get("cc_token"),
        "initial_transaction_id": lustcobox.get("conv_tr_id"),
        "have_first_box": 1 if cint(lustcobox.get("have_first_box")) else 0,
        "month_free": cint(lustcobox.get("second_month_free")),

        "payment_address": doc_billing_address.name,
        "payment_email": doc_billing_address.email_id,
        "payment_phone": doc_billing_address.phone,
        "payment_first_name": doc_billing_address.first_name,
        "payment_last_name": doc_billing_address.last_name,
        "payment_address_1": doc_billing_address.address_line1,
        "payment_address_2": doc_billing_address.address_line2,
        "payment_city": doc_billing_address.city,
        "payment_postcode": doc_billing_address.pincode,
        "payment_country": doc_billing_address.country,
        "payment_zone": doc_billing_address.state,

        "shipping_address": doc_shipping_address.name,
        "shipping_email": doc_shipping_address.email_id,
        "shipping_phone": doc_shipping_address.phone,
        "shipping_first_name": doc_shipping_address.first_name,
        "shipping_last_name": doc_shipping_address.last_name,
        "shipping_address_1": doc_shipping_address.address_line1,
        "shipping_address_2": doc_shipping_address.address_line2,
        "shipping_city": doc_shipping_address.city,
        "shipping_postcode": doc_shipping_address.pincode,
        "shipping_country": doc_shipping_address.country,
        "shipping_zone": doc_shipping_address.state,
    })
    recurring_profile_doc.insert(ignore_permissions=True)


def on_sales_order_added(doc_sales_order, oc_order):
    if sales_order.is_oc_lustcobox_order_doc(doc_sales_order):
        try:
            check_oc_sales_order_totals(doc_sales_order)
            add_lustcobox_order_part(doc_sales_order, oc_order)
            on_lustcobox_order_added(doc_sales_order, oc_order)
            return
        except Exception:
            pass
    try:
        check_oc_sales_order_totals(doc_sales_order)
        if is_pos_payment_method(doc_sales_order.get('oc_pm_code')):
            doc_sales_order.submit()
    except Exception:
        pass
    else:
        # update sales order status in Opencart site
        if doc_sales_order.get('oc_status') == OC_ORDER_STATUS_AWAITING_FULFILLMENT:
            sync_order_status_to_opencart(doc_sales_order, new_order_status=OC_ORDER_STATUS_PROCESSING)

        if is_pos_payment_method(doc_sales_order.get('oc_pm_code')):
            si = sales_order.make_sales_invoice(doc_sales_order.name)
            si.insert()
            si = frappe.get_doc('Sales Invoice', si.name)
            try:
                if is_pos_payment_method(si.oc_pm_code):
                    si.submit()
                else:
                    return
            except Exception as ex:
                frappe.msgprint('Sales Invoice "%s" was not submitted.\n%s' % (si.name, str(ex)))
            else:
                dn = erpnext_sales_invoice.make_delivery_note(si.name)
                dn.insert()
                frappe.msgprint('Delivery Note %s was created automatically' % dn.name)

                ps = make_packing_slip(dn.name)
                ps.get_items()
                ps.insert()
                frappe.msgprint('Packing Slip %s was created automatically' % ps.name)
        else:
            is_credit_ok = check_credit_limit(doc_sales_order.customer, doc_sales_order.company)
            if is_credit_ok:
                pass
                # si = sales_order.make_sales_invoice(doc_sales_order.name)
                # si.insert()
            else:
                so_names = '["' + doc_sales_order.name + '"]'
                erpnext_sales_order.stop_or_unstop_sales_orders(so_names, "Stopped")
    finally:
        frappe.db.set_value('Sales Order', doc_sales_order.name, 'oc_is_auto_processing', 0)


@frappe.whitelist()
def pull_added_from(site_name, silent=False):
    try:
        ret = _pull_added_from(site_name, silent=silent)
    except:
        raise
    else:
        frappe.db.commit()
        return ret


def _pull_added_from(site_name, silent=False):
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = False

    site_doc = frappe.get_doc('Opencart Site', site_name)
    company = site_doc.get('company')
    tax_rate_names = oc_site.get_tax_rate_names(site_name)

    get_order_statuses_success, order_statuses = oc_api.get(site_name, use_pure_rest_api=True).get_order_statuses()
    statuses_to_pull = [doc_status.get('status') for doc_status in site_doc.order_statuses_to_pull]
    name_to_order_status_id_map = {}
    order_status_id_to_name_map = {}
    for order_status in order_statuses:
        name_to_order_status_id_map[order_status.get('name')] = order_status.get('order_status_id')
        order_status_id_to_name_map[order_status.get('order_status_id')] = order_status.get('name')

    # check whether all statuses to pull are in Opencart site
    for status_name_to_pull in statuses_to_pull:
        if not name_to_order_status_id_map.get(status_name_to_pull):
            sync_info([], 'Order Status "%s" cannot be found on this Opencart site' % status_name_to_pull, stop=True)

    default_days_interval = 10
    now_date = datetime.now().date()
    modified_from = site_doc.get('orders_modified_from')
    modified_to = add_days(modified_from, default_days_interval)
    if modified_to > now_date:
        modified_to = add_days(now_date, 1)
    while True:
        success, oc_orders = oc_api.get(site_name).get_orders_addeed_from_to(modified_from.strftime("%Y-%m-%d"), modified_to.strftime("%Y-%m-%d"))
        for oc_order in oc_orders:
            check_count += 1
            order_status_name = order_status_id_to_name_map.get(oc_order.get('order_status_id'))
            if order_status_name not in statuses_to_pull:
                skip_count += 1
                # extras = (1, 'skipped', 'Skipped: Order Status - %s' % order_status_name)
                # results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                continue
            doc_order = get_order(site_name, oc_order.get('order_id'))
            if oc_order.get('customer_id') == '0':
                # trying to get guest customer
                doc_customer = customers.get_guest_customer(site_name, oc_order.get('email'), oc_order.get('firstname'), oc_order.get('lastname'))
                if doc_customer:
                    # update guest customer
                    customers.update_guest_from_order(doc_customer, oc_order)
                else:
                    # create new guest customer
                    doc_customer = customers.create_guest_from_order(site_name, oc_order)
            else:
                doc_customer = customers.get_customer(site_name, oc_order.get('customer_id'))
                if doc_customer:
                    # update customer
                    customers.update_from_oc_order(doc_customer, oc_order)
                else:
                    try:
                        doc_customer = customers.create_from_oc(site_name, oc_order.get('customer_id'), oc_order)
                    except Exception as ex:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: error occurred on getting customer with id "%s".\n%s' % (oc_order.get('customer_id', ''), str(ex)))
                        results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                        continue

            oc_order_type = oc_order.get('order_type')
            if doc_order:
                # update existed Sales Order only with status "Draft"
                if doc_order.docstatus != 0:
                    skip_count += 1
                    continue
                params = {}
                resolve_customer_group_rules(oc_order, doc_customer, params)
                params.update({
                    'oc_order_type': oc_order_type,
                    'currency': oc_order.get('currency_code'),
                    # 'conversion_rate': float(oc_order.currency_value),
                    'base_net_total': oc_order.get('total'),
                    'total': oc_order.get('total'),
                    'company': company,
                    'transaction_date': getdate(oc_order.get('date_added', '')),
                    'oc_is_updating': 1,
                    'oc_status': order_status_name,
                    # payment method
                    'oc_pm_title': oc_order.get('payment_method'),
                    'oc_pm_code': oc_order.get('payment_code'),
                    'oc_pa_firstname': oc_order.get('payment_firstname'),
                    'oc_pa_lastname': oc_order.get('payment_lastname'),
                    'oc_pa_company': oc_order.get('payment_company'),
                    'oc_pa_country_id': oc_order.get('payment_country_id'),
                    'oc_pa_country': oc_order.get('payment_country'),
                    # shipping method
                    'oc_sm_title': oc_order.get('shipping_method'),
                    'oc_sm_code': oc_order.get('shipping_code'),
                    'oc_sa_firstname': oc_order.get('shipping_firstname'),
                    'oc_sa_lastname': oc_order.get('shipping_lastname'),
                    'oc_sa_company': oc_order.get('shipping_company'),
                    'oc_sa_country_id': oc_order.get('shipping_country_id'),
                    'oc_sa_country': oc_order.get('shipping_country'),
                    #
                    'oc_last_sync_from': datetime.now(),
                })

                # updating fiscal year
                fiscal_year = get_fiscal_year(date=getdate(oc_order.get('date_added', '')), company=company)
                if fiscal_year:
                    params.update({'fiscal_year': fiscal_year[0]})

                doc_order.update(params)
                update_totals(doc_order, oc_order, tax_rate_names)
                doc_order.save()
                try:
                    resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
                except Exception as ex:
                    update_count += 1
                    extras = (1, 'updated', 'Updated, but shipping rule is not resolved: %s' % str(ex))
                    results_list.append((doc_order.get('name'),
                                         doc_order.get('oc_order_id'),
                                         doc_order.get_formatted('oc_last_sync_from'),
                                         doc_order.get('modified')) + extras)
                    continue
                update_count += 1
                extras = (1, 'updated', 'Updated')
                results_list.append((doc_order.get('name'),
                                     doc_order.get('oc_order_id'),
                                     doc_order.get_formatted('oc_last_sync_from'),
                                     doc_order.get('modified')) + extras)

            else:
                if not doc_customer:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: missed customer customer_id "%s"' % oc_order.get('customer_id', ''))
                    results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                    continue

                params = {}
                resolve_customer_group_rules(oc_order, doc_customer, params)
                doc_shipping_address = addresses.get_from_oc_order(site_name, doc_customer.name, oc_order, address_type='Shipping')

                # creating new Sales Order
                params.update({
                    'doctype': 'Sales Order',
                    'oc_order_type': oc_order_type,
                    'currency': oc_order.get('currency_code'),
                    'base_net_total': oc_order.get('total'),
                    'total': oc_order.get('total'),
                    'company': company,
                    'customer': doc_customer.name,
                    'transaction_date': getdate(oc_order.get('date_added', '')),
                    'delivery_date': add_days(nowdate(), 7),
                    'shipping_address_name': doc_shipping_address.name,
                    'oc_is_updating': 1,
                    'oc_is_auto_processing': 1,
                    'oc_site': site_name,
                    'oc_order_id': oc_order.get('order_id'),
                    'oc_status': order_status_name,
                    # payment method
                    'oc_pm_title': oc_order.get('payment_method'),
                    'oc_pm_code': oc_order.get('payment_code'),
                    'oc_pa_firstname': oc_order.get('payment_firstname'),
                    'oc_pa_lastname': oc_order.get('payment_lastname'),
                    'oc_pa_company': oc_order.get('payment_company'),
                    'oc_pa_country_id': oc_order.get('payment_country_id'),
                    'oc_pa_country': oc_order.get('payment_country'),
                    # shipping method
                    'oc_sm_title': oc_order.get('shipping_method'),
                    'oc_sm_code': oc_order.get('shipping_code'),
                    'oc_sa_firstname': oc_order.get('shipping_firstname'),
                    'oc_sa_lastname': oc_order.get('shipping_lastname'),
                    'oc_sa_company': oc_order.get('shipping_company'),
                    'oc_sa_country_id': oc_order.get('shipping_country_id'),
                    'oc_sa_country': oc_order.get('shipping_country'),
                    #
                    'oc_sync_from': True,
                    'oc_last_sync_from': datetime.now(),
                    'oc_sync_to': True,
                    'oc_last_sync_to': datetime.now(),
                })

                # updating fiscal year
                fiscal_year = get_fiscal_year(date=getdate(oc_order.get('date_added', '')), company=company)
                if fiscal_year:
                    params.update({'fiscal_year': fiscal_year[0]})

                doc_order = frappe.get_doc(params)
                if not oc_order.get('products'):
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: missed products')
                    results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                    continue

                items_count = 0
                for product in oc_order.get('products'):
                    # doc_item = items.get_item(site_name, product.get('product_id'))
                    product_id = product.get('product_id')
                    product_model = product.get('model', '').strip().upper()
                    doc_item = items.get_item_by_item_code(product_model)

                    # fetching default variant from item
                    if doc_item and doc_item.default_variant:
                        doc_item = frappe.get_doc("Item", doc_item.default_variant)

                    if not doc_item:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: Item "%s" cannot be found for Opencart product with product id "%s"' % (product_model, product_id))
                        results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                        break

                    # price_list_rate = frappe.db.get_value('Item Price', {'price_list': price_list_name, 'item_code': doc_item.get('item_code')}, 'price_list_rate') or 0
                    so_item = {
                        'item_code': doc_item.get('item_code'),
                        # 'base_price_list_rate': price_list_rate,
                        # 'price_list_rate': price_list_rate,
                        'warehouse': doc_order.get('warehouse') or site_doc.get('items_default_warehouse'),
                        'qty': flt(product.get('quantity')),
                        'currency': product.get('currency_code'),
                        'description': product.get('name')
                    }
                    if is_pos_payment_method(doc_order.get('oc_pm_code')) or sales_order.is_oc_lustcobox_order_type(oc_order_type):
                        so_item.update({
                            'base_rate': flt(product.get('price')),
                            'base_amount': flt(product.get('total')),
                            'rate': flt(product.get('price')),
                            'amount': flt(product.get('total')),
                        })
                    doc_order.append('items', so_item)
                    items_count += 1
                else:
                    if not items_count:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: no products')
                        results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                        continue
                    update_totals(doc_order, oc_order, tax_rate_names)
                    if sales_order.is_oc_lustcobox_order_type(oc_order_type):
                        lustcobox = oc_order.get(sales_order.OC_ORDER_TYPE_LUSTCOBOX, {})
                        doc_order.update({
                            "oc_cc_token_id": lustcobox.get("cc_token"),
                            "oc_initial_transaction_id": lustcobox.get("conv_tr_id"),
                            "oc_have_first_box": 1 if cint(lustcobox.get("have_first_box")) else 0
                        })
                        if not frappe.db.get("Credit Card", {"card_token": doc_order.oc_cc_token_id}):
                            add_existed_credit_card({"customer": doc_order.customer, "card_token": doc_order.oc_cc_token_id})
                    doc_order.insert(ignore_permissions=True)
                    try:
                        resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
                    except Exception as ex:
                        add_count += 1
                        extras = (1, 'added', 'Added, but shipping rule is not resolved: %s' % str(ex))
                        results_list.append((doc_order.get('name'),
                                             doc_order.get('oc_order_id'),
                                             doc_order.get_formatted('oc_last_sync_from'),
                                             doc_order.get('modified')) + extras)
                        continue
                    add_count += 1
                    extras = (1, 'added', 'Added')
                    results_list.append((doc_order.get('name'),
                                         doc_order.get('oc_order_id'),
                                         doc_order.get_formatted('oc_last_sync_from'),
                                         doc_order.get('modified')) + extras)

                    # business logic on adding new order from Opencart site
                    doc_order = frappe.get_doc('Sales Order', doc_order.get('name'))
                    on_sales_order_added(doc_order, oc_order)

        if modified_to > now_date:
            break
        modified_from = modified_to
        modified_to = add_days(modified_to, default_days_interval)
        if modified_to > now_date:
            modified_to = add_days(now_date, 1)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


def _pull_by_order_ids(site_name, oc_order_ids):
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = False

    get_order_statuses_success, order_statuses = oc_api.get(site_name, use_pure_rest_api=True).get_order_statuses()
    name_to_order_status_id_map = {}
    order_status_id_to_name_map = {}
    for order_status in order_statuses:
        name_to_order_status_id_map[order_status.get('name')] = order_status.get('order_status_id')
        order_status_id_to_name_map[order_status.get('order_status_id')] = order_status.get('name')

    site_doc = frappe.get_doc('Opencart Site', site_name)
    company = site_doc.get('company')
    tax_rate_names = oc_site.get_tax_rate_names(site_name)

    for oc_order_id in oc_order_ids:
        get_order_success, oc_order = oc_api.get(site_name).get_order_json(oc_order_id)
        order_status_name = order_status_id_to_name_map.get(oc_order.get('order_status_id'))
        check_count += 1
        doc_order = get_order(site_name, oc_order.get('order_id'))
        if oc_order.get('customer_id') == '0':
            # trying to get guest customer
            doc_customer = customers.get_guest_customer(site_name, oc_order.get('email'), oc_order.get('firstname'), oc_order.get('lastname'))
            if doc_customer:
                # update guest customer
                customers.update_guest_from_order(doc_customer, oc_order)
            else:
                # create new guest customer
                doc_customer = customers.create_guest_from_order(site_name, oc_order)
        else:
            doc_customer = customers.get_customer(site_name, oc_order.get('customer_id'))
            if doc_customer:
                # update customer
                customers.update_from_oc_order(doc_customer, oc_order)
            else:
                try:
                    doc_customer = customers.create_from_oc(site_name, oc_order.get('customer_id'), oc_order)
                except Exception as ex:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: error occurred on getting customer with id "%s".\n%s' % (oc_order.get('customer_id', ''), str(ex)))
                    results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                    continue

        oc_order_type = oc_order.get('order_type')
        if doc_order:
            # update existed Sales Order only with status "Draft"
            if doc_order.docstatus != 0:
                skip_count += 1
                continue
            params = {}
            resolve_customer_group_rules(oc_order, doc_customer, params)
            params.update({
                'oc_order_type': oc_order_type,
                'currency': oc_order.get('currency_code'),
                # 'conversion_rate': float(oc_order.currency_value),
                'base_net_total': oc_order.get('total'),
                'total': oc_order.get('total'),
                'company': company,
                'transaction_date': getdate(oc_order.get('date_added', '')),
                'oc_is_updating': 1,
                'oc_status': order_status_name,
                # payment method
                'oc_pm_title': oc_order.get('payment_method'),
                'oc_pm_code': oc_order.get('payment_code'),
                'oc_pa_firstname': oc_order.get('payment_firstname'),
                'oc_pa_lastname': oc_order.get('payment_lastname'),
                'oc_pa_company': oc_order.get('payment_company'),
                'oc_pa_country_id': oc_order.get('payment_country_id'),
                'oc_pa_country': oc_order.get('payment_country'),
                # shipping method
                'oc_sm_title': oc_order.get('shipping_method'),
                'oc_sm_code': oc_order.get('shipping_code'),
                'oc_sa_firstname': oc_order.get('shipping_firstname'),
                'oc_sa_lastname': oc_order.get('shipping_lastname'),
                'oc_sa_company': oc_order.get('shipping_company'),
                'oc_sa_country_id': oc_order.get('shipping_country_id'),
                'oc_sa_country': oc_order.get('shipping_country'),
                #
                'oc_last_sync_from': datetime.now(),
            })

            # updating fiscal year
            fiscal_year = get_fiscal_year(date=getdate(oc_order.get('date_added', '')), company=company)
            if fiscal_year:
                params.update({'fiscal_year': fiscal_year[0]})

            doc_order.update(params)
            update_totals(doc_order, oc_order, tax_rate_names)
            doc_order.save()
            try:
                resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
            except Exception as ex:
                update_count += 1
                extras = (1, 'updated', 'Updated, but shipping rule is not resolved: %s' % str(ex))
                results_list.append((doc_order.get('name'),
                                     doc_order.get('oc_order_id'),
                                     doc_order.get_formatted('oc_last_sync_from'),
                                     doc_order.get('modified')) + extras)
                continue
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_order.get('name'),
                                 doc_order.get('oc_order_id'),
                                 doc_order.get_formatted('oc_last_sync_from'),
                                 doc_order.get('modified')) + extras)

        else:
            if not doc_customer:
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: missed customer customer_id "%s"' % oc_order.get('customer_id', ''))
                results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                continue

            params = {}
            resolve_customer_group_rules(oc_order, doc_customer, params)
            doc_shipping_address = addresses.get_from_oc_order(site_name, doc_customer.name, oc_order, address_type='Shipping')

            # creating new Sales Order
            params.update({
                'doctype': 'Sales Order',
                'oc_order_type': oc_order_type,
                'currency': oc_order.get('currency_code'),
                'base_net_total': oc_order.get('total'),
                'total': oc_order.get('total'),
                'company': company,
                'customer': doc_customer.name,
                'transaction_date': getdate(oc_order.get('date_added', '')),
                'delivery_date': add_days(nowdate(), 7),
                'shipping_address_name': doc_shipping_address.name,
                'oc_is_updating': 1,
                'oc_is_auto_processing': 1,
                'oc_site': site_name,
                'oc_order_id': oc_order.get('order_id'),
                'oc_status': order_status_name,
                # payment method
                'oc_pm_title': oc_order.get('payment_method'),
                'oc_pm_code': oc_order.get('payment_code'),
                'oc_pa_firstname': oc_order.get('payment_firstname'),
                'oc_pa_lastname': oc_order.get('payment_lastname'),
                'oc_pa_company': oc_order.get('payment_company'),
                'oc_pa_country_id': oc_order.get('payment_country_id'),
                'oc_pa_country': oc_order.get('payment_country'),
                # shipping method
                'oc_sm_title': oc_order.get('shipping_method'),
                'oc_sm_code': oc_order.get('shipping_code'),
                'oc_sa_firstname': oc_order.get('shipping_firstname'),
                'oc_sa_lastname': oc_order.get('shipping_lastname'),
                'oc_sa_company': oc_order.get('shipping_company'),
                'oc_sa_country_id': oc_order.get('shipping_country_id'),
                'oc_sa_country': oc_order.get('shipping_country'),
                #
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': True,
                'oc_last_sync_to': datetime.now(),
            })

            # updating fiscal year
            fiscal_year = get_fiscal_year(date=getdate(oc_order.get('date_added', '')), company=company)
            if fiscal_year:
                params.update({'fiscal_year': fiscal_year[0]})

            doc_order = frappe.get_doc(params)
            if not oc_order.get('products'):
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: missed products')
                results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                continue

            items_count = 0
            for product in oc_order.get('products'):
                # doc_item = items.get_item(site_name, product.get('product_id'))
                product_id = product.get('product_id')
                product_model = product.get('model', '').strip().upper()
                doc_item = items.get_item_by_item_code(product_model)

                # fetching default variant from item
                if doc_item and doc_item.default_variant:
                    doc_item = frappe.get_doc("Item", doc_item.default_variant)

                if not doc_item:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: Item "%s" cannot be found for Opencart product with product id "%s"' % (product_model, product_id))
                    results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                    break

                # price_list_rate = frappe.db.get_value('Item Price', {'price_list': price_list_name, 'item_code': doc_item.get('item_code')}, 'price_list_rate') or 0
                so_item = {
                    'item_code': doc_item.get('item_code'),
                    # 'base_price_list_rate': price_list_rate,
                    # 'price_list_rate': price_list_rate,
                    'warehouse': doc_order.get('warehouse') or site_doc.get('items_default_warehouse'),
                    'qty': flt(product.get('quantity')),
                    'currency': product.get('currency_code'),
                    'description': product.get('name')
                }
                if is_pos_payment_method(doc_order.get('oc_pm_code')) or sales_order.is_oc_lustcobox_order_type(oc_order_type):
                    so_item.update({
                        'base_rate': flt(product.get('price')),
                        'base_amount': flt(product.get('total')),
                        'rate': flt(product.get('price')),
                        'amount': flt(product.get('total')),
                    })
                doc_order.append('items', so_item)
                items_count += 1
            else:
                if not items_count:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: no products')
                    results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                    continue
                update_totals(doc_order, oc_order, tax_rate_names)
                if sales_order.is_oc_lustcobox_order_type(oc_order_type):
                    lustcobox = oc_order.get(sales_order.OC_ORDER_TYPE_LUSTCOBOX, {})
                    doc_order.update({
                        "oc_cc_token_id": lustcobox.get("cc_token"),
                        "oc_initial_transaction_id": lustcobox.get("conv_tr_id"),
                        "oc_have_first_box": 1 if cint(lustcobox.get("have_first_box")) else 0
                    })
                    if doc_order.oc_cc_token_id and not frappe.db.get("Credit Card", {"card_token": doc_order.oc_cc_token_id}):
                        add_existed_credit_card({"customer": doc_order.customer, "card_token": doc_order.oc_cc_token_id})
                doc_order.insert(ignore_permissions=True)
                try:
                    resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
                except Exception as ex:
                    add_count += 1
                    extras = (1, 'added', 'Added, but shipping rule is not resolved: %s' % str(ex))
                    results_list.append((doc_order.get('name'),
                                         doc_order.get('oc_order_id'),
                                         doc_order.get_formatted('oc_last_sync_from'),
                                         doc_order.get('modified')) + extras)
                    continue
                add_count += 1
                extras = (1, 'added', 'Added')
                results_list.append((doc_order.get('name'),
                                     doc_order.get('oc_order_id'),
                                     doc_order.get_formatted('oc_last_sync_from'),
                                     doc_order.get('modified')) + extras)

                # business logic on adding new order from Opencart site
                doc_order = frappe.get_doc('Sales Order', doc_order.get('name'))
                on_sales_order_added(doc_order, oc_order)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


def resolve_customer_group_rules(oc_order, doc_customer, params):
    territory_to_price_list_map = {}
    territory_to_warehouse_map = {}
    doc_customer_group = frappe.get_doc('Customer Group', doc_customer.get('customer_group'))
    rules = doc_customer_group.get('oc_customer_group_rule') or []
    for rule in rules:
        if rule.get('rule_condition') == 'If Territory of Customer is':
            parent_territory = rule.get('condition_territory')
            territory_to_price_list_map[parent_territory] = rule.get('action_price_list')
            territory_to_warehouse_map[parent_territory] = rule.get('action_warehouse')

            # child territories of level 1
            child_territories_1 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': parent_territory})
            for territory_1 in child_territories_1:
                territory_to_price_list_map[territory_1.get('name')] = rule.get('action_price_list')
                territory_to_warehouse_map[territory_1.get('name')] = rule.get('action_warehouse')

                # child territories of level 2
                child_territories_2 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': territory_1.get('name')})
                for territory_2 in child_territories_2:
                    territory_to_price_list_map[territory_2.get('name')] = rule.get('action_price_list')
                    territory_to_warehouse_map[territory_2.get('name')] = rule.get('action_warehouse')
    if oc_order.get('shipping_iso_code_3') and oc_order.get('shipping_zone_code'):
        territory_name = territories.get_by_iso_code3(oc_order.get('shipping_iso_code_3'), oc_order.get('shipping_zone_code'))
    else:
        territory_name = territories.get_by_iso_code3(oc_order.get('payment_iso_code_3'), oc_order.get('payment_zone_code'))
    price_list_name = territory_to_price_list_map.get(territory_name, doc_customer_group.get('default_price_list'))
    # doc_price_list = price_lists.get_by_name(site_name, price_list_name)
    warehouse_name = territory_to_warehouse_map.get(territory_name, '')
    if not price_list_name:
        frappe.throw('Please specify Default Price List for Customer Group "%s"' % cstr(doc_customer_group.get('customer_group_name')))

    if territory_name != doc_customer.get('territory'):
        doc_customer.update({'territory': territory_name})
        doc_customer.update({'oc_is_updating': 1})
        doc_customer.save()

    params.update({
        'territory': territory_name,
        'selling_price_list': price_list_name,
        # 'price_list_currency': doc_price_list.get('currency'),
        'warehouse': warehouse_name,
    })


@frappe.whitelist()
def resolve_price_list_and_warehouse(customer, doc_customer=None):
    if doc_customer is None:
        doc_customer = frappe.get_doc('Customer', customer)
    territory_to_price_list_map = {}
    territory_to_warehouse_map = {}
    doc_customer_group = frappe.get_doc('Customer Group', doc_customer.get('customer_group'))
    rules = doc_customer_group.get('oc_customer_group_rule')
    for rule in rules:
        if rule.get('rule_condition') == 'If Territory of Customer is':
            parent_territory = rule.get('condition_territory')
            territory_to_price_list_map[parent_territory] = rule.get('action_price_list')
            territory_to_warehouse_map[parent_territory] = rule.get('action_warehouse')

            # child territories of level 1
            child_territories_1 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': parent_territory})
            for territory_1 in child_territories_1:
                territory_to_price_list_map[territory_1.get('name')] = rule.get('action_price_list')
                territory_to_warehouse_map[territory_1.get('name')] = rule.get('action_warehouse')

                # child territories of level 2
                child_territories_2 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': territory_1.get('name')})
                for territory_2 in child_territories_2:
                    territory_to_price_list_map[territory_2.get('name')] = rule.get('action_price_list')
                    territory_to_warehouse_map[territory_2.get('name')] = rule.get('action_warehouse')
    territory = doc_customer.get('territory')
    price_list_name = territory_to_price_list_map.get(territory, doc_customer_group.get('default_price_list'))
    # doc_price_list = price_lists.get_by_name(site_name, price_list_name)
    warehouse_name = territory_to_warehouse_map.get(territory, '')
    if not price_list_name:
        frappe.throw('Please specify Default Price List for Customer Group "%s"' % cstr(doc_customer_group.get('customer_group_name')))

    return {
        'territory': territory,
        'price_list': price_list_name,
        # 'price_list_currency': doc_price_list.get('currency'),
        'warehouse': warehouse_name,
    }


@frappe.whitelist()
def get_customer_selling_info(customer, doc_customer=None):
    res = resolve_price_list_and_warehouse(customer, doc_customer=doc_customer)
    res.update({'company': frappe.db.get_value('Warehouse', res.get('warehouse'), 'company') if res.get('warehouse') else ''})
    return res


@frappe.whitelist()
def resolve_shipping_rule(customer, db_customer=None, doc_customer=None, doc_oc_store=None):
    if db_customer is not None:
        obj_customer = db_customer
    elif doc_customer is not None:
        obj_customer = doc_customer
    elif customer:
        obj_customer = frappe.db.get('Customer', customer)
    else:
        return

    if obj_customer.get('shipping_rule'):
        return obj_customer.get('shipping_rule')

    oc_site = obj_customer.get('oc_site')
    customer_group = obj_customer.get('customer_group')

    shipping_rule = frappe.db.get_value('Customer Group', customer_group, 'shipping_rule')
    if shipping_rule:
        return shipping_rule

    if oc_site:
        # resolve shipping rule for customr from Opencart site
        if not obj_customer.get('territory'):
            return
        # resolve doc_oc_store
        if doc_oc_store is None:
            doc_oc_store = oc_stores.get(oc_site, obj_customer.get('oc_store_id'))
            if not doc_oc_store:
                # frappe.msgprint('Cannot resolve Shipping Rule: Customer does not belong to any of Opencart stores')
                return
        for doc_oc_shipping_rule in doc_oc_store.get('oc_shipping_rules'):
            doc_shipping_rule = frappe.get_doc('Shipping Rule', doc_oc_shipping_rule.get('shipping_rule'))
            if doc_shipping_rule.worldwide_shipping:
                return doc_shipping_rule.name
            for doc_shipping_rule_country in doc_shipping_rule.get('countries'):
                customer_country = frappe.db.get_value("Territory", obj_customer.get('territory'), "country")
                if customer_country and doc_shipping_rule_country.country == customer_country:
                    return doc_shipping_rule.name
    else:
        # resolve shipping rule for ERPNext customer
        shipping_rules = frappe.get_all('Shipping Rule', filters={'customer_group': customer_group})
        if len(shipping_rules) > 1:
            frappe.msgprint('Found %d Shipping Rules with Customer Group set to "%s". Chosen the first Shipping Rule in the list.' % (len(shipping_rules), customer_group))
            return shipping_rules[0].get('name')
        elif len(shipping_rules) == 1:
            return shipping_rules[0].get('name')


@frappe.whitelist()
def resolve_taxes_and_charges(customer, company, db_customer=None, doc_customer=None):
    if db_customer is not None:
        obj_customer = db_customer
    elif doc_customer is not None:
        obj_customer = doc_customer
    elif customer:
        obj_customer = frappe.db.get('Customer', customer)
    else:
        return

    template = sales_taxes_and_charges_template.get_first_by_territory(obj_customer.get('territory'), company_name=company)
    if not template:
        frappe.msgprint('Please specify Sales Taxes and Charges Template for territory "%s"' % (obj_customer.get('territory'), ))
        return
    return template


def resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company):
    # taxes related part
    template = resolve_taxes_and_charges(doc_customer.get('name'), company, doc_customer=doc_customer)
    if not template:
        frappe.throw('Cannot resolve Sales Taxes and Charges Template for "%s" Territory, order id "%s"' % (doc_customer.get('territory'), oc_order.get('order_id')))

    # shipping related part
    doc_oc_store = oc_stores.get(site_name, oc_order.get('store_id'))
    if not doc_oc_store:
        frappe.throw('Cannot resolve Opencart Store for site "{}" and with store id "{}"'.format(site_name, oc_order.get('store_id')))
    shipping_rule = resolve_shipping_rule(doc_customer.get('name'), doc_customer=doc_customer, doc_oc_store=doc_oc_store)
    if not shipping_rule:
        frappe.throw('Cannot resolve Shipping Rule for Opencart Store "%s" and Territory "%s" and customer from "%s" Customer Group' % (doc_oc_store.get('name'), doc_customer.get('territory'), doc_customer.get('customer_group')))

    doc_order.update({
        'oc_is_shipping_included_in_total': 1,
        'taxes_and_charges': template or '',
        'shipping_rule': shipping_rule or ''
    })
    doc_order.calculate_taxes_and_totals()
    doc_order.update({'oc_is_updating': 1})
    doc_order.save()
