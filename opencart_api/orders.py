from __future__ import unicode_literals
from datetime import datetime
import re

import frappe
from frappe.utils import add_days, nowdate, cstr

import oc_api
import customers
import warehouses
import items


def get_order(site_name, oc_order_id):
    db_order = frappe.db.get("Sales Order", {"oc_site": site_name, "oc_order_id": oc_order_id})
    if db_order:
        return frappe.get_doc('Sales Order', db_order.get("name"))


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

    site_doc = frappe.get_doc("Opencart Site", site_name)
    company = site_doc.get('company')

    db_customers = frappe.db.sql("""select oc_customer_id from `tabCustomer` where oc_site = '%s'""" % site_name, as_dict=1)
    for db_customer in db_customers:
        for oc_order in oc_api.get(site_name).get_orders_by_customer(db_customer.get('oc_customer_id')):
            check_count += 1
            doc_order = get_order(site_name, oc_order.id)
            if doc_order:
                # update existed Sales Order
                params = {
                    'currency': oc_order.currency_code,
                    'conversion_rate': float(oc_order.currency_value),
                    'total': oc_order.total,
                    'company': company,
                    "oc_last_sync_from": datetime.now(),
                }
                doc_order.update(params)
                doc_order.save()
                update_count += 1
                extras = (1, 'updated', 'Updated')
                results_list.append((doc_order.get('name'),
                                     doc_order.get('oc_order_id'),
                                     doc_order.get_formatted('oc_last_sync_from'),
                                     doc_order.get('modified')) + extras)

            else:
                # creating new Sales Order
                doc_customer = customers.get_customer(site_name, oc_order.customer_id)
                if not doc_customer:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: missed customer')
                    results_list.append(('', oc_order.id, '', '') + extras)
                    continue
                params = {
                    'doctype': 'Sales Order',
                    'currency': oc_order.currency_code,
                    'conversion_rate': float(oc_order.currency_value),
                    'total': oc_order.total,
                    'company': company,
                    'customer': doc_customer.name,
                    'delivery_date': add_days(nowdate(), 15),
                    'oc_site': site_name,
                    'oc_order_id': oc_order.id,
                    "oc_sync_from": True,
                    "oc_last_sync_from": datetime.now(),
                    "oc_sync_to": True,
                    "oc_last_sync_to": datetime.now(),
                }

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
                        break

                    doc_order.append("items", {
                        "item_code": doc_item.get('item_code'),
                        "warehouse": site_doc.get("default_warehouse"),
                        "qty": product.get('quantity'),
                        "rate": product.get('price'),
                        "amount": product.get('total'),
                        "currency": product.get('currency_code'),
                        "description": product.get('name')
                    })
                    items_count += 1
                if not items_count:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: no products')
                    results_list.append(('', oc_order.id, '', '') + extras)
                    continue
        # {
        # "order_product_id":"14",
        # "product_id":"63",
        # "name":"Durazest For Men 10 Pack",
        # "model":"",
        # "sku":"",
        # "option":[],
        # "quantity":"3",
        # "price":"59.99$ USD",
        # "total":"179.97$ USD"
        # }

                doc_order.insert(ignore_permissions=True)
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
