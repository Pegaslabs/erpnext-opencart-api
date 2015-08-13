from datetime import datetime

import frappe

import oc_api


def get_item_group(site_name, oc_category_id):
    db_item_group = frappe.db.get('Item Group', {'oc_site': site_name, 'oc_category_id': oc_category_id})
    if db_item_group:
        return frappe.get_doc('Item Group', db_item_group.get('name'))


@frappe.whitelist()
def pull_categories_from_oc(site_name, silent=False):
    results = {}
    results_list = []
    check_count = 0
    add_count = 0
    update_count = 0
    skip_count = 0
    success = True

    site_doc = frappe.get_doc('Opencart Site', site_name)
    root_item_group = site_doc.get('root_item_group')
    opencart_api = oc_api.get(site_name)
    doc_root_item_group = frappe.get_doc('Item Group', root_item_group)
    for oc_category in opencart_api.get_all_categories():
        # if not doc_root_item_group.get('oc_category_id'):
        #     doc_root_item_group.update({'oc_category_id': oc_category.id})
        #     doc_root_item_group.save()
        check_count += 1
        doc_item_group = get_item_group(site_name, oc_category.id)
        doc_parent_item_group = doc_root_item_group
        if oc_category.parent_id:
            doc_parent_item_group = get_item_group(site_name, oc_category.parent_id)

        if not doc_parent_item_group:
            skip_count += 1
            extras = (1, 'skipped', 'Skipped: parent group missed')
            results_list.append((oc_category.name, '', oc_category.id, '', '') + extras)
            continue

        if doc_item_group:
            # update existed Item Group
            params = {
                'description': oc_category.description,
                'show_in_website': 1,
                'parent_item_group': doc_parent_item_group.get('name'),
                'oc_last_sync_from': datetime.now()
            }
            doc_item_group.update(params)
            doc_item_group.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_item_group.get('name'),
                                 doc_item_group.get('parent_item_group'),
                                 doc_item_group.get('oc_category_id') or '',
                                 doc_item_group.get_formatted('oc_last_sync_from') or '',
                                 doc_item_group.get('modified') or '') + extras)
        else:
            # checking whether item group name is unique
            db_item_group = frappe.db.get('Item Group', {'name': oc_category.name})
            if db_item_group:
                # it means that the group with such name already exists
                # but the oc_category_id is missed or is different than from Opencart site
                doc_item_group = frappe.get_doc('Item Group', oc_category.name)
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: duplicate name')
                results_list.append((oc_category.name, doc_parent_item_group.get('name'), oc_category.id, '', '') + extras)
                continue
            else:
                # creating new Item Group
                params = {
                    'doctype': 'Item Group',
                    'oc_site': site_name,
                    'item_group_name': oc_category.name,
                    'parent_item_group': doc_parent_item_group.get('name'),
                    'oc_category_id': oc_category.id,
                    'description': oc_category.description,
                    'show_in_website': 'Yes',
                    'oc_sync_from': True,
                    'oc_last_sync_from': datetime.now(),
                    'oc_sync_to': True,
                    'oc_last_sync_to': datetime.now(),
                    'is_group': 'Yes'
                }
                doc_item_group = frappe.get_doc(params)
                doc_item_group.insert(ignore_permissions=True)
                add_count += 1
                extras = (1, 'added', 'Added')
                results_list.append((doc_item_group.get('name'),
                                    doc_item_group.get('parent_item_group'),
                                    doc_item_group.get('oc_category_id') or '',
                                    doc_item_group.get_formatted('oc_last_sync_from') or '',
                                    doc_item_group.get('modified') or '') + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


def get_all_by_oc_site(site_name):
    return frappe.db.sql('''select name, oc_category_id from `tabItem Group` where oc_site=%(site_name)s''', {'site_name': site_name}, as_dict=1)
