from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_stores
import customer_groups
import items
import oc_api


def get(item_code, price_list):
    db_item_price = frappe.db.get("Item Price", {"item_code": item_code, "price_list": price_list})
    if db_item_price:
        return frappe.get_doc('Item Price', db_item_price.get("name"))


def oc_validate(doc, method=None):
    if doc.get('oc_is_updating', 1):
        doc.update({'oc_is_updating': 0})
        return
    db_item = frappe.db.get('Item', doc.get('item_code'))
    if not (db_item and db_item.get('oc_site') and db_item.get('oc_sync_to')):
        return

    db_price_list = frappe.db.get('Price List', doc.get('price_list'))
    if not db_price_list:
        return

    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': doc.get('price_list')})
    if not db_oc_price_list:
        return

    site_name = db_item.get('oc_site')
    doc_item = frappe.get_doc('Item', db_item.get('name'))
    oc_product_id = doc_item.get('oc_product_id')
    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
    get_product_success, oc_product = oc_api.get(site_name).get_product(oc_product_id)

    if not db_oc_store.get('oc_store_front_url'):
        frappe.msgprint('Warning. Store front url is not set it Opencart Store "%s"' % db_oc_store.get('name'))

    if db_oc_price_list.get('is_master'):
        # updating price as product main price on Opencart site
        doc_item.update({'oc_price': doc.get('price_list_rate')})
        # it is going to update main price on Opencart site
        doc_item.save()
    else:
        # updating or creating price as discount on Opencart site
        doc_customer_group = frappe.get_doc('Customer Group', db_oc_price_list.get('customer_group'))
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        items.update_or_create_item_discount(doc_item, {
            'customer_group_id': customer_group_id,
            'price': doc.get('price_list_rate'),
            'priority': '0',
            'quantity': '1',
            'date_start': '',
            'date_end': '',
        })
        # it is going to update discount price on Opencart site
        doc_item.save()


@frappe.whitelist()
def pull(site_name, silent=False):
    '''Sync Item Prices from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    doc_stores = oc_stores.get_all(site_name)
    oc_api_cache = {}
    customer_groups_cache = {}

    for doc_store in doc_stores:
        if doc_store.get('oc_store_front_url') and doc_store.get('oc_price_lists'):
            oc_api_cache[doc_store.get('name')] = oc_api.get(site_name, doc_store.get('oc_store_front_url'))

            # fill cache of customer groups
            for doc_oc_price_list in doc_store.get('oc_price_lists'):
                customer_group_name = doc_oc_price_list.get('customer_group')
                doc_customer_group = frappe.get_doc('Customer Group', customer_group_name)
                customer_groups_cache[doc_customer_group.get('name')] = doc_customer_group

    for dict_item in items.get_all_dict(site_name, fields=['name', 'item_code', 'oc_product_id']):
        item_code = dict_item.get('item_code')
        for doc_store in doc_stores:
            oc_api_obj = oc_api_cache.get(doc_store.get('name'))
            if oc_api_obj:
                get_product_success, oc_product = oc_api_obj.get_product(dict_item.get('oc_product_id'))
                if not get_product_success:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: cannot get product with product_id %s' % dict_item.get('oc_product_id'))
                    results_list.append(('', '', '', '', '') + extras)
                    continue
                doc_item = frappe.get_doc('Item', dict_item.get('name'))
                items.update_item(doc_item, oc_product, save=True)
            for doc_oc_price_list in doc_store.get('oc_price_lists'):
                check_count += 1
                price_list_name = doc_oc_price_list.get('price_list')
                customer_group_name = doc_oc_price_list.get('customer_group')
                doc_price_list = frappe.get_doc('Price List', price_list_name)
                doc_item_price = get(item_code, price_list_name)

                # resolve price
                price = float(oc_product.get('price', 0))
                customer_group_id = customer_groups_cache.get(customer_group_name, {}).get('oc_customer_group_id')
                for discount in oc_product.get('discounts'):
                    if customer_group_id == discount.get('customer_group_id') and int(discount.get('quantity', 0)) == 1:
                        price = float(discount.get('price', 0))
                if doc_item_price:
                    # update existed Item Price
                    doc_item_price.update({
                        'price_list_rate': price,
                        'oc_is_updating': 1
                    })
                    doc_item_price.save()
                    update_count += 1
                    extras = (1, 'updated', 'Updated')
                    results_list.append((doc_item_price.get('name'),
                                        doc_item_price.get('item_code'),
                                        doc_item_price.get('price_list'),
                                        doc_item_price.get('currency'),
                                        doc_item_price.get('price_list_rate')) + extras)
                else:
                    # validating
                    if doc_price_list.get('currency') != oc_product.get('currency_code'):
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: currency inconsistency: "%s" and "%s"' % (doc_price_list.get('currency'), oc_product.get('currency_code')))
                        results_list.append(('', '', '', '', '') + extras)
                        continue

                    # create new Item Price
                    params = {
                        'doctype': 'Item Price',
                        'oc_is_updating': 1,
                        'selling': 1,
                        'item_code': item_code,
                        'price_list': price_list_name,
                        'price_list_rate': price
                    }
                    doc_item_price = frappe.get_doc(params)
                    doc_item_price.insert(ignore_permissions=True)
                    add_count += 1
                    extras = (1, 'added', 'Added')
                    results_list.append((doc_item_price.get('name'),
                                        doc_item_price.get('item_code'),
                                        doc_item_price.get('price_list'),
                                        doc_item_price.get('currency'),
                                        doc_item_price.get('price_list_rate')) + extras)
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
def get_oc_related_stores(site_name):
    '''Get related stores of Opencart site'''
    stores = frappe.db.sql("""select name, oc_store_id, oc_last_sync_from, modified, oc_last_sync_from from `tabOpencart Store` where oc_site=%(site_name)s""", {"site_name": site_name})
    return stores
