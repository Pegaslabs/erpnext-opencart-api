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

    oc_warehouse_success, oc_warehouses = oc_api.get(site_name, use_pure_rest_api=False).get_warehouses()
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
def clear_file_data(name):
    all_file_data = frappe.get_all('File', filters={'attached_to_doctype': 'Warehouse', 'attached_to_name': name})
    for file_data in all_file_data:
        frappe.get_doc('File', file_data.get('name')).delete()


@frappe.whitelist()
def update_inventory(warehouse, item_code_from, update_bin_location, bin_location_from, update_barcode, barcode_from):
    results = {}
    res_items = []
    try:
        rows = read_csv_content_from_attached_file(frappe.get_doc('Warehouse', warehouse))
    except:
        frappe.throw(_('Please select a valid csv file with data'))

    is_header_detected = False
    item_code_idx = 0
    bin_location_idx = 0
    barcode_idx = 0
    for row in rows:
        if not is_header_detected:
            try:
                robust_row = ['' if field is None else field.lower().strip() for field in row]
                item_code_idx = map(lambda a: a.startswith(item_code_from.lower().strip()), robust_row).index(True)
                if update_bin_location:
                    bin_location_idx = map(lambda a: a.startswith(bin_location_from.lower().strip()), robust_row).index(True)
                if update_barcode:
                    barcode_idx = map(lambda a: a.startswith(barcode_from.lower().strip()), robust_row).index(True)
            except ValueError:
                continue
            else:
                is_header_detected = True
                continue

        item_code = row[item_code_idx] or ''
        item_code = item_code.upper().strip()
        bin_location = row[bin_location_idx] or ''
        bin_location = bin_location.strip()
        barcode = row[barcode_idx] or ''
        barcode = barcode.strip()
        status_message = ''

        if not item_code or (bin_location in ['-', '', None] and barcode in ['-', '', None]):
            continue

        # update Bin with new bin location
        if update_bin_location:
            db_bin = frappe.db.get('Bin', {'item_code': item_code, 'warehouse': warehouse})
            if db_bin:
                if bin_location in ['-', '', None]:
                    status_message += '\Bin Location is not invalid.'
                else:
                    frappe.db.set_value('Bin', db_bin.get('name'), 'bin_location', bin_location)
                    status_message += 'Bin Location is updated.'
            else:
                status_message += 'Bin was not updated: Bin with Item Code "%s" and Warehouse "%s" not found.' % (item_code, warehouse)

        # update Item with new barcode
        if update_barcode:
            db_item = frappe.db.get('Item', {'name': item_code})
            if db_item:
                if barcode in ['-', '', None]:
                    status_message += '\nBarcode is not invalid.'
                else:
                    frappe.db.set_value('Item', db_item.get('name'), 'barcode', barcode)
                    status_message += '\nBarcode is updated.'
            else:
                status_message += '\nItem was not updated: Item with Item Code "%s" not found.' % (item_code,)

        item = {'item_code': item_code, 'bin_location': bin_location, 'barcode': barcode, 'status_message': status_message}
        res_items.append(item)

    results['items'] = res_items
    return results
