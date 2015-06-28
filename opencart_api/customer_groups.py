from datetime import datetime

import frappe

import oc_api


def get(site_name, oc_customer_group_id):
    db_item_group = frappe.db.get('Customer Group', {'oc_site': site_name, 'oc_customer_group_id': oc_customer_group_id})
    if db_item_group:
        return frappe.get_doc('Customer Group', db_item_group.get('name'))


def get_all_by_oc_site(site_name):
    return frappe.db.sql('''select name, oc_customer_group_id from `tabCustomer Group` where oc_site=%(site_name)s''', {'site_name': site_name}, as_dict=1)


@frappe.whitelist()
def pull(site_name, silent=False):
    results = {}
    results_list = []
    check_count = 0
    add_count = 0
    update_count = 0
    skip_count = 0
    success = True

    site_doc = frappe.get_doc('Opencart Site', site_name)
    root_customer_group = site_doc.get('root_customer_group')
    opencart_api = oc_api.get(site_name)
    for oc_customer_group in opencart_api.get_customer_groups():
        check_count += 1
        doc_customer_group = get(site_name, oc_customer_group.id)
        if doc_customer_group:
            # update existed Customer Group
            doc_customer_group = frappe.get_doc('Customer Group', oc_customer_group.name)
            params = {
                'doctype': 'Customer Group',
                'customer_group_name': oc_customer_group.name,
                'description': oc_customer_group.description,
                'oc_last_sync_from': datetime.now(),
            }
            doc_customer_group.update(params)
            doc_customer_group.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_customer_group.get('name'),
                                doc_customer_group.get('parent_customer_group'),
                                doc_customer_group.get('oc_customer_group_id'),
                                doc_customer_group.get_formatted('oc_last_sync_from'),
                                doc_customer_group.get('modified') or '') + extras)
        else:
            params = {
                'doctype': 'Customer Group',
                'oc_site': site_name,
                'oc_customer_group_id': oc_customer_group.id,
                'customer_group_name': oc_customer_group.name,
                'description': oc_customer_group.description,
                'parent_customer_group': root_customer_group,
                'is_group': 'Yes',
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': True,
                'oc_last_sync_to': datetime.now()
            }
            doc_customer_group = frappe.get_doc(params)

            # check if whether Customer Group name is unique or not
            if frappe.db.get('Customer Group', {'name': oc_customer_group.name}):
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: duplicate name')
                results_list.append((oc_customer_group.name,
                                    doc_customer_group.get('parent_customer_group'),
                                    doc_customer_group.get('oc_customer_group_id'),
                                    doc_customer_group.get_formatted('oc_last_sync_from'),
                                    doc_customer_group.get('modified') or '') + extras)
                continue
            else:
                # creating new Customer Group
                doc_customer_group.insert(ignore_permissions=True)
                add_count += 1
                extras = (1, 'added', 'Added')
                results_list.append((doc_customer_group.get('name'),
                                    doc_customer_group.get('parent_customer_group'),
                                    doc_customer_group.get('oc_customer_group_id'),
                                    doc_customer_group.get_formatted('oc_last_sync_from'),
                                    doc_customer_group.get('modified') or '') + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results
