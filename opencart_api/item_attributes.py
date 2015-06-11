from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_api


def fix_unique_name(initial_name):
    name = initial_name
    counter = 1
    while True:
        if frappe.db.get('Item Attribute', {'name': name}):
            name += ' (%d)' % counter
            continue
        break
    return name


def get(site_name, oc_option_id):
    db_item_attr = frappe.db.get('Item Attribute', {'oc_site': site_name, 'oc_option_id': oc_option_id})
    if db_item_attr:
        return frappe.get_doc('Item Attribute', db_item_attr.get('name'))


def get_value(site_name, oc_option_value_id):
    db_item_attr_value = frappe.db.get('Item Attribute Value', {'oc_site': site_name, 'oc_option_value_id': oc_option_value_id})
    if db_item_attr_value:
        return frappe.get_doc('Item Attribute Value', db_item_attr_value.get('name'))


@frappe.whitelist()
def pull(site_name, silent=False):
    '''Sync Item Attributes from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = False

    for oc_product_option in oc_api.get(site_name).get_product_options():
        check_count += 1
        doc_item_attr = get(site_name, oc_product_option.id)
        if doc_item_attr:
            # update existed Item Attribute
            # check here for a need to update Item Attribute
            params = {
                'attribute_name': oc_product_option.name,
                'oc_last_sync_from': datetime.now(),
            }
            doc_item_attr.update(params)
            doc_item_attr.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_item_attr.get('name'),
                                 doc_item_attr.get('oc_option_id'),
                                 doc_item_attr.get_formatted('oc_last_sync_from'),
                                 doc_item_attr.get('modified')) + extras)
        else:
            item_attribute_values = []
            for option_val in oc_product_option.option_values_list:
                item_attribute_values.append({
                    'attribute_value': option_val.name,
                    'abbr': option_val.name,
                    'oc_site': site_name,
                    'oc_option_value_id': option_val.option_value_id,
                    'oc_image': option_val.image,
                    'oc_thumb': option_val.thumb
                })
            params = {
                'doctype': 'Item Attribute',
                'attribute_name': oc_product_option.name,
                'item_attribute_values': item_attribute_values,
                'oc_site': site_name,
                'oc_option_id': oc_product_option.id,
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': True,
                'oc_last_sync_to': datetime.now()
            }
            doc_item_attr = frappe.get_doc(params)
            # check if whether Item Attribute name is unique or not
            if frappe.db.get('Item Attribute', {'name': oc_product_option.name}):
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: duplicate name')
                results_list.append((oc_product_option.name,
                                     oc_product_option.id,
                                     '',
                                     '') + extras)
                continue
            else:
                # creating new Item Attribute
                doc_item_attr.insert(ignore_permissions=True)
                add_count += 1
                extras = (1, 'added', 'Added')
                results_list.append((doc_item_attr.get('name'),
                                     doc_item_attr.get('oc_option_id'),
                                     doc_item_attr.get_formatted('oc_last_sync_from'),
                                     doc_item_attr.get('modified')) + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results
