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


def resolve_site_from_item_price(doc_item_price):
    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': doc_item_price.get('price_list')})
    if not db_oc_price_list:
        return
    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
    return db_oc_store.get('oc_site')


def update_item(doc_item, doc_item_price):
    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': doc_item_price.get('price_list')})
    if not db_oc_price_list:
        return
    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
    site_name = db_oc_store.get('oc_site')
    doc_oc_product = items.get_opencart_product(site_name, doc_item.get('name'))
    if not db_oc_store.get('oc_store_front_url'):
        frappe.msgprint('Warning. Store front url is not set it Opencart Store "%s"' % db_oc_store.get('name'))

    if db_oc_price_list.get('is_master'):
        # updating price as product main price on Opencart site
        doc_oc_product.update({'oc_price': float(doc_item_price.get('price_list_rate'))})
        # it is going to update main price on Opencart site
        doc_oc_product.save()
    else:
        # updating or creating price as discount on Opencart site
        db_customer_group = frappe.db.get('Customer Group', {'name': db_oc_price_list.get('customer_group')})
        if not db_customer_group:
            frappe.msgprint('Customer Group is not set for Opencart Price List in Opencart Store "%s"' % db_oc_store.get('name'))
        customer_group_id = db_customer_group.get('oc_customer_group_id')
        items.update_or_create_item_discount(site_name, doc_item, {
            'customer_group_id': customer_group_id,
            'price': doc_item_price.get('price_list_rate'),
            'priority': '0',
            'quantity': '1',
            'date_start': '',
            'date_end': '',
        }, save=True, is_updating=True)


def oc_validate(doc, method=None):
    if doc.get('oc_is_updating', 1):
        doc.update({'oc_is_updating': 0})
        return
    db_item = frappe.db.get('Item', doc.get('item_code'))
    if not (db_item and db_item.get('oc_sync_to')):
        return
    doc_item = frappe.get_doc('Item', db_item.get('name'))
    update_item(doc_item, doc)

    # push Item to Opencart site
    site_name = resolve_site_from_item_price(doc)
    doc_item = frappe.get_doc('Item', doc_item.get('name'))
    items.push_item_to_oc(doc_item, site_name)


@frappe.whitelist()
def pull(site_name, item_code=None, silent=False):
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
            print('store name=' + doc_store.get('oc_store_front_url'))
            # fill cache of customer groups
            for doc_oc_price_list in doc_store.get('oc_price_lists'):
                customer_group_name = doc_oc_price_list.get('customer_group')
                db_customer_group = frappe.db.get('Customer Group', {'name': customer_group_name})
                if not db_customer_group:
                    frappe.msgprint('Customer Group is not set for Opencart Price List in Opencart Store "%s"' % doc_store.get('name'))
                    continue
                customer_groups_cache[db_customer_group.get('name')] = db_customer_group

    all_dict_items = []
    if item_code:
        all_dict_items = frappe.get_all('Item', fields=['name', 'item_code'], filters={'item_code': item_code.upper()})
    else:
        all_dict_items = frappe.get_all('Item', fields=['name', 'item_code'])
    items_count_left_to_process = len(all_dict_items)
    for dict_item in all_dict_items:
    # for dict_item in [it for it in frappe.get_all('Item', fields=['name', 'item_code']) if it.get('name') == 'TESTAH']:
        item_code = dict_item.get('item_code')
        items_count_left_to_process -= 1
        print('processing %s, left to process %d' % (item_code or '', items_count_left_to_process))
        doc_oc_product = items.get_opencart_product(site_name, dict_item.get('name'))
        if not doc_oc_product:
            skip_count += 1
            continue
        oc_product_id = doc_oc_product.get('oc_product_id')
        doc_item = frappe.get_doc('Item', dict_item.get('name'))
        for doc_store in doc_stores:
            oc_api_obj = oc_api_cache.get(doc_store.get('name'))
            if oc_api_obj:
                get_product_success, oc_product = oc_api_obj.get_product(oc_product_id)
                if not get_product_success:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: cannot get product with product_id %s' % oc_product_id)
                    results_list.append(('', '', '', '', '') + extras)
                    continue
            # TODO
            # updating item for each store
            # items.update_item(site_name, doc_item, oc_product, save=True, is_updating=True)
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

                update_item(doc_item, doc_item_price)
        # get again updated Item and pushing it to Opencart site
        doc_item = frappe.get_doc('Item', doc_item.get('name'))
        items.push_item_to_oc(doc_item, site_name)

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
