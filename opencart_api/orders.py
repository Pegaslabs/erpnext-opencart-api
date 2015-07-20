from __future__ import unicode_literals
from datetime import datetime
import re

import frappe
from frappe.utils import add_days, nowdate, getdate, cstr
from frappe.exceptions import ValidationError

from utils import sync_info
from decorators import sync_to_opencart
import oc_api
import oc_site
import customers
import oc_stores
import items
import territories
import sales_taxes_and_charges_template


OC_ORDER_STATUS_AWAITING_FULFILLMENT = 'Awaiting Fulfillment'
OC_ORDER_STATUS_PROCESSING = 'Processing'
OC_ORDER_STATUS_SHIPPED = 'Shipped'
OC_ORDER_STATUS_COMPLETE = 'Complete'
OC_ORDER_STATUS_CANCELED = 'Canceled'


OC_CURRENCY_REGEX = re.compile("([A-Z]{3})")
OC_TOTAL_REGEX = re.compile("([\d,.]+)")

TOTALS_PRECISION = 0.001


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


@sync_to_opencart
def before_save(doc, method=None):
    sync_order_to_opencart(doc)


@sync_to_opencart
def on_submit(doc, method=None):
    if doc.get('oc_check_totals'):
        oc_sub_total = get_rate_from_total_str(doc.get('oc_sub_total') or '')
        oc_shipping_total = get_rate_from_total_str(doc.get('oc_shipping_total') or '')
        oc_tax_total = get_rate_from_total_str(doc.get('oc_tax_total') or '')
        oc_total = get_rate_from_total_str(doc.get('oc_total') or '')

        if not are_totals_equal(doc.get('total'), oc_sub_total):
            frappe.throw('%s: Order\'s Total ($%s) does not equal to Sub Total ($%s) from Opencart site' % (doc.get('name'), str(doc.get('total')), str(oc_sub_total)))
        if not are_totals_equal(doc.get('total_taxes_and_charges'), oc_shipping_total + oc_tax_total):
            frappe.throw('%s: Order\'s Total Taxes and Charges ($%s) does not equal to sum of Shipping Total ($%s) and Tax Total ($%s) from Opencart site' % (doc.get('name'), str(doc.get('total_taxes_and_charges')), str(oc_shipping_total), str(oc_tax_total)))
        if not are_totals_equal(doc.get('grand_total'), oc_total):
            frappe.throw('%s: Order\'s Total ($%s) does not equal to Sub Total ($%s) from Opencart site' % (doc.get('name'), str(doc.get('grand_total')), str(oc_total)))

    # frappe.db.set(doc, 'oc_status', OC_ORDER_STATUS_PROCESSING)
    # sync_order_to_opencart(doc)

    # # update Opencart status
    # if doc_order.get('status') is None or doc_order.get('status') == 'Draft':
    # elif doc_order.get('status') == 'Submitted':
    # elif doc_order.get('status') == 'Stopped':
    # elif doc_order.get('status') == 'Cancelled':


@sync_to_opencart
def on_cancel(doc, method=None):
    frappe.db.set(doc, 'oc_status', OC_ORDER_STATUS_CANCELED)
    sync_order_status_to_opencart(doc)


@sync_to_opencart
def on_trash(doc, method=None):
    site_name = doc.get('oc_site')
    oc_order_id = doc.get('oc_order_id')
    success, resp = oc_api.get(site_name).delete_order(oc_order_id)
    if success:
        frappe.msgprint('Order was deleted successfully on Opencart site')
    else:
        frappe.msgprint('Order is not deleted on Opencart site. Error: %s' % resp.get('error', 'Unknown'))


def sync_order_status_to_opencart(doc_order):
    site_name = doc_order.get('oc_site')
    oc_order_id = doc_order.get('oc_order_id')
    get_order_success, oc_order = oc_api.get(site_name).get_order_json(oc_order_id)

    order_status_id = oc_site.get_order_status_id(site_name, doc_order.get('oc_status'))
    if oc_order_id and get_order_success and oc_order_id == oc_order.get('order_id'):
        # update existed order on Opencart site
        data = {'status': order_status_id}
        success, resp = oc_api.get(site_name).update_order(oc_order_id, data)
        if success:
            frappe.msgprint('Order status "%s" is updated successfully on Opencart site' % doc_order.get('oc_status'))
            doc_order.update({'oc_last_sync_to': datetime.now()})
        else:
            frappe.msgprint('Order status "%s" is not updated on Opencart site.\nError: %s' % (doc_order.get('oc_status'), resp.get('error', 'Unknown')))


def sync_order_to_opencart(doc_order):
    site_name = doc_order.get('oc_site')
    # validating customer
    customer_name = doc_order.get('customer')
    doc_customer = frappe.get_doc('Customer', customer_name)
    oc_customer_id = doc_customer.get('oc_customer_id')
    if not oc_customer_id:
        frappe.throw('To sync Order to Opencart Site, Customer "%s" should be existed on Opencart Site' % cstr(customer_name))
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
    shipping_total = ''
    tax_rate_name = ''
    tax_total = ''
    total = ''
    for t in oc_order.get('totals', []):
        if t.get('title') == 'Sub-Total':
            sub_total = t.get('text')
        elif t.get('title') == 'Shipping':
            shipping_total = t.get('text')
        elif t.get('title') == 'Total':
            total = t.get('text')
        elif t.get('title') in tax_rate_names or t.get('title') == 'VAT':
            tax_rate_name = t.get('title')
            tax_total = t.get('text')
        else:
            frappe.msgprint('Unknown total entity "%s" for order %s' % (t.get('title'), oc_order.get('order_id')))

    doc_order.update({
        'oc_sub_total': sub_total,
        'oc_shipping_total': shipping_total,
        'oc_tax_rate_name': tax_rate_name,
        'oc_tax_total': tax_total,
        'oc_total': total
    })


def on_order_added(doc_order):
    try:
        on_submit(doc_order)
        doc_order.submit()
    except ValidationError:
        pass


@frappe.whitelist()
def pull_modified_from(site_name, silent=False):
    '''Sync orders from Opencart site'''
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
        success, oc_orders = oc_api.get(site_name).get_orders_modified_from_to(modified_from.strftime("%Y-%m-%d"), modified_to.strftime("%Y-%m-%d"))
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

            if doc_order:
                # update existed Sales Order with status "Draft"
                if doc_order.get('status') != 'Draft':
                    skip_count += 1
                    continue
                params = {}
                resolve_customer_group_rules2(oc_order, doc_customer, params)
                params.update({
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
                    # shipping method
                    'oc_sm_title': oc_order.get('shipping_method'),
                    'oc_sm_code': oc_order.get('shipping_code'),
                    'oc_sa_firstname': oc_order.get('shipping_firstname'),
                    'oc_sa_lastname': oc_order.get('shipping_lastname'),
                    'oc_sa_company': oc_order.get('shipping_company'),
                    #
                    'oc_last_sync_from': datetime.now(),
                })
                doc_order.update(params)
                update_totals(doc_order, oc_order, tax_rate_names)
                doc_order.save()
                try:
                    resolve_shipping_rule_and_taxes2(oc_order, doc_order, doc_customer, site_name, company)
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
                resolve_customer_group_rules2(oc_order, doc_customer, params)

                # creating new Sales Order
                params.update({
                    'doctype': 'Sales Order',
                    'currency': oc_order.get('currency_code'),
                    'base_net_total': oc_order.get('total'),
                    'total': oc_order.get('total'),
                    'company': company,
                    'customer': doc_customer.name,
                    'transaction_date': getdate(oc_order.get('date_added', '')),
                    'delivery_date': add_days(nowdate(), 7),
                    'oc_is_updating': 1,
                    'oc_site': site_name,
                    'oc_order_id': oc_order.get('order_id'),
                    'oc_status': order_status_name,
                    # payment method
                    'oc_pm_title': oc_order.get('payment_method'),
                    'oc_pm_code': oc_order.get('payment_code'),
                    'oc_pa_firstname': oc_order.get('payment_firstname'),
                    'oc_pa_lastname': oc_order.get('payment_lastname'),
                    'oc_pa_company': oc_order.get('payment_company'),
                    # shipping method
                    'oc_sm_title': oc_order.get('shipping_method'),
                    'oc_sm_code': oc_order.get('shipping_code'),
                    'oc_sa_firstname': oc_order.get('shipping_firstname'),
                    'oc_sa_lastname': oc_order.get('shipping_lastname'),
                    'oc_sa_company': oc_order.get('shipping_company'),
                    #
                    'oc_sync_from': True,
                    'oc_last_sync_from': datetime.now(),
                    'oc_sync_to': True,
                    'oc_last_sync_to': datetime.now(),
                })
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
                    product_model = product.get('model', '').upper()
                    doc_item = items.get_item_by_item_code(product_model)
                    if not doc_item:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: Item "%s" cannot be found for Opencart product with  product id "%s"' % (product_model, product_id))
                        results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                        break

                    # price_list_rate = frappe.db.get_value('Item Price', {'price_list': price_list_name, 'item_code': doc_item.get('item_code')}, 'price_list_rate') or 0
                    doc_order.append('items', {
                        'item_code': doc_item.get('item_code'),
                        # 'base_price_list_rate': price_list_rate,
                        # 'price_list_rate': price_list_rate,
                        'warehouse': site_doc.get('items_default_warehouse'),
                        'qty': product.get('quantity'),
                        'base_rate': product.get('price'),
                        'base_amount': product.get('total'),
                        'rate': product.get('price'),
                        'amount': product.get('total'),
                        'currency': product.get('currency_code'),
                        # 'discount_percentage': 10.0,
                        'description': product.get('name')
                    })
                    items_count += 1
                else:
                    if not items_count:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: no products')
                        results_list.append(('', oc_order.get('order_id'), '', '') + extras)
                        continue
                    update_totals(doc_order, oc_order, tax_rate_names)
                    doc_order.insert(ignore_permissions=True)
                    try:
                        resolve_shipping_rule_and_taxes2(oc_order, doc_order, doc_customer, site_name, company)
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
                    on_order_added(doc_order)

        if modified_to > now_date:
            break
        modified_from = add_days(modified_to, 1)
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


@frappe.whitelist()
def pull_orders_from_oc(site_name, silent=False):
    '''Sync orders from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = False

    site_doc = frappe.get_doc('Opencart Site', site_name)
    company = site_doc.get('company')

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

    db_customers = frappe.db.sql('select oc_customer_id from `tabCustomer` where oc_site = \'%s\'' % site_name, as_dict=1)
    for db_customer in db_customers:
        for oc_order in oc_api.get(site_name).get_orders_by_customer(db_customer.get('oc_customer_id')):
            check_count += 1
            order_status_name = order_status_id_to_name_map.get(oc_order.order_status_id)
            if order_status_name not in statuses_to_pull:
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: Order Status - %s' % order_status_name)
                results_list.append(('', oc_order.id, '', '') + extras)
                continue
            doc_order = get_order(site_name, oc_order.id)
            doc_customer = customers.get_customer(site_name, oc_order.customer_id)
            if doc_order:
                # update existed Sales Order
                params = {}
                resolve_customer_group_rules(oc_order, doc_customer, params)

                params.update({
                    'currency': oc_order.currency_code,
                    # 'conversion_rate': float(oc_order.currency_value),
                    'base_net_total': oc_order.total,
                    'total': oc_order.total,
                    'company': company,
                    'oc_is_updating': 1,
                    'oc_status': order_status_name,
                    'oc_last_sync_from': datetime.now(),
                })
                doc_order.update(params)
                doc_order.save()
                resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
                update_count += 1
                extras = (1, 'updated', 'Updated')
                results_list.append((doc_order.get('name'),
                                     doc_order.get('oc_order_id'),
                                     doc_order.get_formatted('oc_last_sync_from'),
                                     doc_order.get('modified')) + extras)

            else:
                if not doc_customer:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: missed customer')
                    results_list.append(('', oc_order.id, '', '') + extras)
                    continue

                params = {}
                resolve_customer_group_rules(oc_order, doc_customer, params)

                # creating new Sales Order
                params.update({
                    'doctype': 'Sales Order',
                    'currency': oc_order.currency_code,
                    'base_net_total': oc_order.total,
                    'total': oc_order.total,
                    'company': company,
                    'customer': doc_customer.name,
                    'delivery_date': add_days(nowdate(), 7),
                    'oc_is_updating': 1,
                    'oc_site': site_name,
                    'oc_order_id': oc_order.id,
                    'oc_status': order_status_name,
                    'oc_sync_from': True,
                    'oc_last_sync_from': datetime.now(),
                    'oc_sync_to': True,
                    'oc_last_sync_to': datetime.now(),
                })
                doc_order = frappe.get_doc(params)
                if not oc_order.products:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: missed products')
                    results_list.append(('', oc_order.id, '', '') + extras)
                    continue

                items_count = 0
                for product in oc_order.products:
                    doc_item = items.get_item(site_name, product.get('product_id'))
                    if not doc_item:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: Item "%s", product id "%s" cannot be found' % (product.get('name'), product.get('product_id')))
                        results_list.append(('', oc_order.id, '', '') + extras)
                        break
                    if doc_item.get('has_variants'):
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: Item "%s", product id "%s" is a tempalte' % (product.get('name'), product.get('product_id')))
                        results_list.append(('', oc_order.id, '', '') + extras)
                        break

                    # price_list_rate = frappe.db.get_value('Item Price', {'price_list': price_list_name, 'item_code': doc_item.get('item_code')}, 'price_list_rate') or 0
                    doc_order.append('items', {
                        'item_code': doc_item.get('item_code'),
                        # 'base_price_list_rate': price_list_rate,
                        # 'price_list_rate': price_list_rate,
                        'warehouse': site_doc.get('items_default_warehouse'),
                        'qty': product.get('quantity'),
                        'base_rate': product.get('price'),
                        'base_amount': product.get('total'),
                        'rate': product.get('price'),
                        'amount': product.get('total'),
                        'currency': product.get('currency_code'),
                        # 'discount_percentage': 10.0,
                        'description': product.get('name')
                    })
                    items_count += 1
                else:
                    if not items_count:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: no products')
                        results_list.append(('', oc_order.id, '', '') + extras)
                        continue

                    doc_order.insert(ignore_permissions=True)
                    resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company)
                    add_count += 1
                    extras = (1, 'added', 'Added')
                    results_list.append((doc_order.get('name'),
                                         doc_order.get('oc_order_id'),
                                         doc_order.get_formatted('oc_last_sync_from'),
                                         doc_order.get('modified')) + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


def resolve_customer_group_rules2(oc_order, doc_customer, params):
        territory_to_price_list_map = {}
        territory_to_warehouse_map = {}
        doc_customer_group = frappe.get_doc('Customer Group', doc_customer.get('customer_group'))
        rules = doc_customer_group.get('oc_customer_group_rule')
        for rule in rules:
            if rule.get('condition') == 'If Territory of Customer is':
                parent_territory = rule.get('condition_territory')
                territory_to_price_list_map[parent_territory] = rule.get('action_price_list')
                territory_to_warehouse_map[parent_territory] = rule.get('action_warehouse')

                # child territories of level 1
                child_territories_1 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': parent_territory})
                for territory_1 in child_territories_1:
                    territory_to_price_list_map[territory_1.get('name')] = rule.get('action_price_list')
                    territory_to_warehouse_map[territory_1.get('name')] = rule.get('action_warehouse')

                    # child territories of level 2
                    child_territories_2 = frappe.get_all('Territory', fields=['name'], filters={'parent_territory': territory_1})
                    for territory_2 in child_territories_2:
                        territory_to_price_list_map[territory_2.get('name')] = rule.get('action_price_list')
                        territory_to_warehouse_map[territory_2.get('name')] = rule.get('action_warehouse')

        territory_name = territories.get_by_iso_code3(oc_order.get('shipping_iso_code_3'), oc_order.get('shipping_zone_code'))
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


def resolve_customer_group_rules(oc_order, doc_customer, params):
        territory_to_price_list_map = {}
        territory_to_warehouse_map = {}
        doc_customer_group = frappe.get_doc('Customer Group', doc_customer.get('customer_group'))
        rules = doc_customer_group.get('oc_customer_group_rule')
        for rule in rules:
            if rule.get('condition') == 'If Territory of Customer is':
                territory_to_price_list_map[rule.get('condition_territory')] = rule.get('action_price_list')
                territory_to_warehouse_map[rule.get('condition_territory')] = rule.get('action_warehouse')

        territory_name = territories.get_by_iso_code3(oc_order.shipping_iso_code_3, oc_order.shipping_zone_code)
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
def resolve_shipping_rule(customer, db_customer=None, doc_customer=None, doc_oc_store=None):
    if db_customer is not None:
        obj_customer = db_customer
    elif doc_customer is not None:
        obj_customer = doc_customer
    elif customer:
        obj_customer = frappe.db.get('Customer', customer)
    else:
        return

    if not obj_customer.get('oc_site'):
        frappe.msgprint('Cannot resolve Shipping Rule: Customer does not have any Opencart Site set')
        return

    # resolve doc_oc_store
    if doc_oc_store is None:
        doc_oc_store = oc_stores.get(obj_customer.get('oc_site'), obj_customer.get('oc_store_id'))
        if not doc_oc_store:
            frappe.msgprint('Cannot resolve Shipping Rule: Customer does not belong to any of Opencart stores')
            return

    # check for strong coincidence
    # frappe.msgprint('territory=' + str(obj_customer.get('territory') + str(doc_oc_store.get('name'))))
    for doc_oc_shipping_rule in doc_oc_store.get('oc_shipping_rules'):
        doc_shipping_rule = frappe.get_doc('Shipping Rule', doc_oc_shipping_rule.get('shipping_rule'))
        # frappe.msgprint('doc_shipping_rule=' + str(doc_shipping_rule.get('name')))
        for doc_applicable_territory in doc_shipping_rule.get('territories'):
            # frappe.msgprint('doc_applicable_territory.territory=' + str(doc_applicable_territory.territory))
            if doc_applicable_territory.territory == obj_customer.get('territory'):
                return doc_shipping_rule.get('name')

    # check for non-strong coincidence, take into account the territory hierarchy
    for doc_oc_shipping_rule in doc_oc_store.get('oc_shipping_rules'):
        doc_shipping_rule = frappe.get_doc('Shipping Rule', doc_oc_shipping_rule.get('shipping_rule'))
        for doc_applicable_territory in doc_shipping_rule.get('territories'):
            parent_territory = frappe.get_doc('Territory', obj_customer.get('territory')).get('parent_territory')
            while parent_territory:
                if doc_applicable_territory.territory == parent_territory:
                    return doc_shipping_rule.get('name')
                parent_territory = frappe.get_doc('Territory', parent_territory).get('parent_territory')
    frappe.msgprint('Shipping Rule is not resolved')


@frappe.whitelist()
def resolve_taxes_and_charges(customer, db_customer=None, doc_customer=None):
    if db_customer is not None:
        obj_customer = db_customer
    elif doc_customer is not None:
        obj_customer = doc_customer
    elif customer:
        obj_customer = frappe.db.get('Customer', customer)
    else:
        return

    if not obj_customer.get('oc_site'):
        frappe.msgprint('Cannot resolve Taxes and Charges: Customer does not have any Opencart Site set')
        return
    doc_site = frappe.get_doc('Opencart Site', obj_customer.get('oc_site'))
    doc_template = sales_taxes_and_charges_template.get_first_by_territory(obj_customer.get('territory'), company_name=doc_site.get('company'))
    if not doc_template:
        frappe.msgprint('Please specify Sales Taxes and Charges Template for territory "%s"' % (obj_customer.get('territory'), ))
        return
    return doc_template.get('name')


def resolve_shipping_rule_and_taxes2(oc_order, doc_order, doc_customer, site_name, company):
        # taxes related part
        template = resolve_taxes_and_charges(doc_customer.get('name'), doc_customer=doc_customer)
        if not template:
            frappe.throw('Cannot resolve Sales Taxes and Charges Template for "%s" Territory, order id "%s"' % (doc_customer.get('territory'), oc_order.get('order_id')))

        # shipping related part
        doc_oc_store = oc_stores.get(site_name, oc_order.get('store_id'))
        shipping_rule = resolve_shipping_rule(doc_customer.get('name'), doc_customer=doc_customer, doc_oc_store=doc_oc_store)
        if not shipping_rule:
            frappe.throw('Cannot resolve Shipping Rule for Opencart Store "%s" and Territory "%s" and customer from "%s" Customer Group' % (doc_oc_store.get('name'), doc_customer.get('territory'), doc_customer.get('customer_group')))

        doc_order.update({
            'taxes_and_charges': template or '',
            'shipping_rule': shipping_rule or ''
        })

        tax_item = None
        shipping_item = None
        taxes_len = len(doc_order.taxes)

        doc_order.set_taxes()
        doc_order.calculate_taxes_and_totals()
        if len(doc_order.get('taxes')) > taxes_len:
            tax_item = doc_order.get('taxes')[-1]

        taxes_len = len(doc_order.taxes)
        doc_order.apply_shipping_rule()
        if len(doc_order.get('taxes')) > taxes_len:
            shipping_item = doc_order.get('taxes')[-1]

        if tax_item and shipping_item:
            old_tax_item_idx = tax_item.get('idx')
            old_shipping_item_idx = shipping_item.get('idx')
            tax_item.update({
                'idx': old_shipping_item_idx,
            })
            shipping_item.update({
                'idx': old_tax_item_idx
            })
            tax_item.update({
                'charge_type': 'On Previous Row Total',
                'row_id': shipping_item.get('idx')
            })
            doc_order.update({'oc_is_updating': 1})
            doc_order.save()
            doc_order = frappe.get_doc('Sales Order', doc_order.get('name'))
            doc_order.calculate_taxes_and_totals()

        doc_order.update({'oc_is_updating': 1})
        doc_order.save()


def resolve_shipping_rule_and_taxes(oc_order, doc_order, doc_customer, site_name, company):
        # taxes related part
        doc_template = sales_taxes_and_charges_template.get_first_by_territory(doc_customer.get('territory'), company_name=company)

        # shipping related part
        doc_store = oc_stores.get(site_name, oc_order.store_id)

        doc_order.update({
            # 'apply_discount_on': 'Net Total',
            # 'discount_amount': 35.0,
            'taxes_and_charges': doc_template.get('name') or '',
            'shipping_rule': doc_store.get('oc_shipping_rule') or ''
        })

        # doc_order.append_taxes_from_master()
        doc_order.set_taxes()
        doc_order.calculate_taxes_and_totals()

        doc_order.apply_shipping_rule()
        doc_order.calculate_taxes_and_totals()
        doc_order.update({'oc_is_updating': 1})
        doc_order.save()
