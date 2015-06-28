from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_api


def get(site_name, oc_store_id):
    db_opencart_store = frappe.db.get('Opencart Store', {'oc_site': site_name, 'oc_store_id': oc_store_id})
    if db_opencart_store:
        return frappe.get_doc('Opencart Store', db_opencart_store.get('name'))


def get_all(site_name):
    return [frappe.get_doc('Opencart Store', db_store.get('name')) for db_store in frappe.get_all('Opencart Store')]


@frappe.whitelist()
def pull(site_name, silent=False):
    '''Sync stores from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    for oc_store in oc_api.get(site_name, use_pure_rest_api=True).get_stores():
        check_count += 1
        doc_oc_store = get(site_name, oc_store.id)
        if doc_oc_store:
            # update existed Opencart Store
            # check here for a need to update Opencart Store
            params = {
                'store_name': oc_store.name,
                'oc_last_sync_from': datetime.now(),
            }
            doc_oc_store.update(params)
            doc_oc_store.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_oc_store.get('name'),
                                doc_oc_store.get('oc_store_id'),
                                doc_oc_store.get_formatted('oc_last_sync_from') or '',
                                doc_oc_store.get('modified') or '') + extras)

        else:
            # creating new Opencart Store
            params = {
                'doctype': 'Opencart Store',
                'name': oc_store.name,
                'store_name': oc_store.name,
                'oc_site': site_name,
                'oc_store_id': oc_store.id,
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now()
            }
            doc_oc_store = frappe.get_doc(params)
            doc_oc_store.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_oc_store.get('name'),
                                doc_oc_store.get('oc_store_id'),
                                doc_oc_store.get_formatted('oc_last_sync_from') or '',
                                doc_oc_store.get('modified') or '') + extras)
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
    stores = frappe.db.sql('''select name, oc_store_id, oc_last_sync_from, modified, oc_last_sync_from from `tabOpencart Store` where oc_site=%(site_name)s''', {'site_name': site_name})
    return stores
