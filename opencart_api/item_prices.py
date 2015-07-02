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
        doc.update({'oc_is_updating': '0'})
        return

    db_item = frappe.db.get('Item', doc.get('item_code'))
    if not (db_item and db_item.get('oc_site') and db_item.get('oc_sync_to')):
        return

    db_price_list = frappe.db.get('Price List', doc.get('price_list'))
    if not db_price_list:
        return

    # check if it's a master price list
    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': doc.get('price_list')})
    if not(db_oc_price_list and db_oc_price_list.get('is_master')):
        return

    # updating product with discounts
    site_name = db_item.get('oc_site')
    doc_item = frappe.get_doc('Item', db_item.get('name'))
    oc_product_id = doc_item.get('oc_product_id')
    get_product_success, oc_product = oc_api.get(site_name).get_product(oc_product_id)

    data = {}
    if oc_product_id and get_product_success:
        # discounts
        product_discount = []
        for doc_oc_discount in doc.oc_discounts:
            doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
            customer_group_id = doc_customer_group.get('oc_customer_group_id')
            if not customer_group_id:
                continue
            product_discount.append({
                'customer_group_id': customer_group_id,
                'price': doc_oc_discount.price,
                'priority': doc_oc_discount.priority,
                'quantity': doc_oc_discount.quantity,
                'date_start': doc_oc_discount.date_start,
                'date_end': doc_oc_discount.date_end,
            })
        if product_discount:
            data['product_discount'] = product_discount

        # update existed product on Opencart site
        success = oc_api.get(site_name).update_product(oc_product_id, data)
        if success:
            frappe.msgprint('Product\'s discounts are updated successfully on Opencart site')
            doc_item.update({'oc_last_sync_to': datetime.now()})
        else:
            frappe.msgprint('Product\'s discounts are not updated on Opencart site. Error: Unknown')
    else:
        frappe.msgprint('Product\'s discounts are updated on Opencart. Error: such product does not exist.')


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
                customer_group_name = doc_oc_price_list.get('oc_customer_group')
                if customer_group_name:
                    doc_customer_group = frappe.get('Customer Group', customer_group_name)
                    customer_groups_cache[doc_customer_group.get('oc_customer_group_id')] = doc_customer_group

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

            for doc_oc_price_list in doc_store.get('oc_price_lists'):
                check_count += 1
                is_master_price_list = doc_oc_price_list.get('is_master')
                price_list_name = doc_oc_price_list.get('price_list')
                doc_price_list = frappe.get_doc('Price List', price_list_name)
                doc_item_price = get(item_code, price_list_name)

                # resolve price for the proper price list
                price = float(oc_product.get('price', 0))
                customer_group_name = doc_price_list.get('oc_customer_group')
                if customer_group_name:
                    customer_group = frappe.get_doc('Customer Group', customer_group_name)
                    customer_group_id = customer_group.get('oc_customer_group_id')
                    for discount in oc_product.get('discounts'):
                        if customer_group_id == discount.get('customer_group_id') and int(discount.get('quantity', 0)) < 2:
                            price = float(discount.get('price', 0))

                if doc_item_price:
                    # update existed Item Price
                    doc_item_price.update({
                        'price_list_rate': price,
                        'oc_is_updating': 1
                    })
                    if is_master_price_list:
                        # discounts
                        doc_item_price.set('oc_discounts', [])
                        for discount in oc_product.get('discounts'):
                            customer_group = customer_groups.get(site_name, discount.get('customer_group_id'))
                            if not customer_group:
                                extras = (1, 'skipped', 'Skipped discounts: missed Customer Group with customer_group_id "%s"' % (discount.get('customer_group_id'),))
                                results_list.append(('', '', '', '', '') + extras)
                                continue
                            doc_item_price.append('oc_discounts', {
                                'item_name': dict_item.get('name'),
                                'customer_group': customer_group.get('name'),
                                'quantity': discount.get('quantity'),
                                'priority': discount.get('priority'),
                                'price': discount.get('price'),
                                'date_start': discount.get('date_start'),
                                'date_end': discount.get('date_end'),
                            })
                    doc_item_price.save()

                    skip_count += 1
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

                    if is_master_price_list:
                        # discounts
                        for discount in oc_product.get('discounts'):
                            customer_group = customer_groups.get(site_name, discount.get('customer_group_id'))
                            if not customer_group:
                                extras = (1, 'skipped', 'Skipped discounts: missed Customer Group with customer_group_id "%s"' % (discount.get('customer_group_id'),))
                                results_list.append(('', '', '', '', '') + extras)
                                continue
                            doc_item_price.append('oc_discounts', {
                                'item_name': dict_item.get('name'),
                                'customer_group': customer_group.get('name'),
                                'quantity': discount.get('quantity'),
                                'priority': discount.get('priority'),
                                'price': discount.get('price'),
                                'date_start': discount.get('date_start'),
                                'date_end': discount.get('date_end'),
                            })
                        doc_item_price.save()
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
