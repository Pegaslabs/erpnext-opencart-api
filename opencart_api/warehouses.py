from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_api


def get(site_name, oc_warehouse_id):
    db_opencart_warehouse = frappe.db.get('Warehouse', {'oc_site': site_name, 'oc_warehouse_id': oc_warehouse_id})
    if db_opencart_warehouse:
        return frappe.get_doc('Warehouse', db_opencart_warehouse.get('name'))


def get_all(site_name):
    return [frappe.get_doc('Warehouse', db_warehouse.get('name')) for db_warehouse in frappe.get_all('Warehouse', filters={'oc_site': site_name})]


@frappe.whitelist()
def pull(site_name, silent=False):
    '''Sync warehouses from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    oc_warehouse_success, oc_warehouses = oc_api.get(site_name, use_pure_rest_api=True).get_warehouse_json()
    for oc_warehouse in oc_warehouses:
        check_count += 1
        doc_oc_warehouse = get(site_name, oc_warehouse.get('warehouse_id'))
        if doc_oc_warehouse:
            # update existed Opencart Warehouse
            # check here for a need to update Opencart Warehouse
            params = {
                'warehouse_name': oc_warehouse.get('warehouse_name'),
                'oc_last_sync_from': datetime.now(),
            }
            doc_oc_warehouse.update(params)
            doc_oc_warehouse.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_oc_warehouse.get('warehouse_name'),
                                doc_oc_warehouse.get('oc_warehouse_id'),
                                doc_oc_warehouse.get_formatted('oc_last_sync_from') or '',
                                doc_oc_warehouse.get('modified') or '') + extras)

        else:
            # creating new Opencart Warehouse
            params = {
                'doctype': 'Warehouse',
                'warehouse_name': oc_warehouse.get('warehouse_name'),
                'oc_site': site_name,
                'oc_warehouse_id': oc_warehouse.get('id'),
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now()
            }
            doc_oc_warehouse = frappe.get_doc(params)
            doc_oc_warehouse.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_oc_warehouse.get('warehouse_name'),
                                doc_oc_warehouse.get('oc_warehouse_id'),
                                doc_oc_warehouse.get_formatted('oc_last_sync_from') or '',
                                doc_oc_warehouse.get('modified') or '') + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results
