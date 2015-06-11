from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_api


def get_warehouse(site_name, oc_store_id):
    db_warehouse = frappe.db.get("Warehouse", {"oc_site": site_name, "oc_store_id": oc_store_id})
    if db_warehouse:
        return frappe.get_doc('Warehouse', db_warehouse.get("name"))


@frappe.whitelist()
def pull_warehouses_from_oc(site_name, silent=False):
    '''Sync warehouses from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    site_doc = frappe.get_doc("Opencart Site", site_name)
    default_company = site_doc.get('company')
    for oc_store in oc_api.get(site_name).get_stores():
        check_count += 1
        doc_warehouse = get_warehouse(site_name, oc_store.id)
        if doc_warehouse:
            # update existed Warehouse
            # check here for a need to update Warehouse
            params = {
                "company": default_company,
                "oc_last_sync_from": datetime.now(),
            }
            doc_warehouse.update(params)
            doc_warehouse.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_warehouse.get('name'),
                                doc_warehouse.get('oc_store_id'),
                                doc_warehouse.get_formatted('oc_last_sync_from') or '',
                                doc_warehouse.get('modified') or '') + extras)

        else:
            # creating new Warehouse
            params = {
                "doctype": "Warehouse",
                "warehouse_name": 'OC Store ' + oc_store.id + ' - ' + oc_store.name,
                "company": default_company,
                "oc_site": site_name,
                "oc_store_id": oc_store.id,
                "oc_sync_from": True,
                "oc_last_sync_from": datetime.now(),
                "oc_sync_to": True,
                "oc_last_sync_to": datetime.now(),
            }
            doc_warehouse = frappe.get_doc(params)
            doc_warehouse.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_warehouse.get('name'),
                                doc_warehouse.get('oc_store_id'),
                                doc_warehouse.get_formatted('oc_last_sync_from') or '',
                                doc_warehouse.get('modified') or '') + extras)
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
def get_oc_related_warehouses(site_name):
    '''Get related warehouses of Opencart site'''
    warehouses = frappe.db.sql("""select name, oc_store_id, oc_last_sync_from, modified, oc_last_sync_from from `tabWarehouse` where oc_site=%(site_name)s""", {"site_name": site_name})
    return warehouses
