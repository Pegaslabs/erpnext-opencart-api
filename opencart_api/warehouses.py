from __future__ import unicode_literals
from datetime import datetime

import frappe
from frappe import _
from frappe.utils.csvutils import read_csv_content_from_attached_file

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


@frappe.whitelist()
def update_inventory(doc_name):
    res_items = []
    try:
        rows = read_csv_content_from_attached_file(frappe.get_doc('Warehouse', doc_name))
    except:
        frappe.throw(_('Please select a valid csv file with data'))

    frappe.throw(str(rows[:10]))
    # detect item_code, quantity, description
    is_header_detected = False
    item_code_idx = 0
    quantity_idx = 0
    cost_idx = 0
    description_idx = 0
    for row in rows:
        if not is_header_detected:
            try:
                robust_row = ['' if field is None else field.lower().strip() for field in row]
                item_code_idx = map(lambda a: a.startswith('item no') or a.startswith('item code'), robust_row).index(True)
                quantity_idx = map(lambda a: a.startswith('quantity'), robust_row).index(True)
                cost_idx = map(lambda a: a.startswith('cost'), robust_row).index(True)
                description_idx = map(lambda a: a.startswith('description'), robust_row).index(True)
            except ValueError:
                continue
            else:
                is_header_detected = True
                continue

        item_code = row[item_code_idx]
        # quantity
        quantity = row[quantity_idx]
        if isinstance(quantity, basestring):
            quantity = quantity.strip().replace(',', '')
            quantity = float(quantity) if quantity else None

        # cost
        cost = row[cost_idx]
        if isinstance(cost, basestring):
            cost = cost.strip().replace(',', '')
            cost = float(cost) if cost else None

        description = row[description_idx]
        if item_code is None or quantity is None or description is None or cost is None:
            continue

        item_code = item_code.upper().strip()
        list_item = frappe.get_list('Item', fields=['name', 'item_name'], filters={'is_stock_item': 'Yes', 'name': item_code})
        if not list_item:
            continue
        item = list_item[0]
        item.item_code = item.name
        item.oc_item_name = item.item_name
        item.warehouse = doc_name
        item.qty = quantity
        item.valuation_rate = cost
        item.current_qty = quantity
        item.current_valuation_rate = cost
        del item['name']
        res_items.append(item)

    return res_items
