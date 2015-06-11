from __future__ import unicode_literals
from datetime import datetime

import frappe

import oc_api
import customer_groups


def get_customer(site_name, oc_customer_id):
    db_customer = frappe.db.get("Customer", {"oc_site": site_name, "oc_customer_id": oc_customer_id})
    if db_customer:
        return frappe.get_doc('Customer', db_customer.get("name"))


@frappe.whitelist()
def pull_customers_from_oc(site_name, silent=False):
    '''Sync customers from Opencart site'''
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = False

    site_doc = frappe.get_doc("Opencart Site", site_name)
    # root_customer_group = site_doc.get('root_customer_group')
    default_customer_territory = site_doc.get('default_customer_territory') or "All Territories"
    doc_customer_groups_cache = {}
    for oc_customer in oc_api.get(site_name).get_customers():
        check_count += 1
        doc_customer_group = doc_customer_groups_cache.get(oc_customer.customer_group_id)
        if not doc_customer_group:
            doc_customer_group = customer_groups.get(site_name, oc_customer.customer_group_id)
            doc_customer_groups_cache[oc_customer.customer_group_id] = doc_customer_group

        if not doc_customer_group:
            update_count += 1
            extras = (1, 'skipped', 'Skipped: parent group missed')
            results_list.append((oc_customer.name,
                                 oc_customer.id,
                                 '',
                                 '',
                                 '') + extras)
            continue

        doc_customer = get_customer(site_name, oc_customer.id)
        if doc_customer:
            # update existed Customer
            # check here for a need to update Customer
            params = {
                'customer_group': doc_customer_group.get('name'),
                "oc_last_sync_from": datetime.now(),
                'oc_firstname': oc_customer.firstname,
                'oc_lastname': oc_customer.lastname,
                'oc_telephone': oc_customer.telephone,
                'oc_fax': oc_customer.fax,
                'oc_email': oc_customer.email,
            }
            doc_customer.update(params)
            doc_customer.save()
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_customer.get('name'),
                                 doc_customer.get('oc_customer_id'),
                                 doc_customer_group.get('name'),
                                 doc_customer.get_formatted('oc_last_sync_from'),
                                 doc_customer.get('modified')) + extras)

        else:
            default_price_list = doc_customer_group.get('default_price_list')
            # do not allow to aad new customer if default_price_list is missed in customer's group
            if not default_price_list:
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: missed default price list in customer group')
                results_list.append((oc_customer.name,
                                     oc_customer.id,
                                     '',
                                     '',
                                     '') + extras)
                continue

            # create new Customer
            params = {
                "doctype": "Customer",
                "customer_type": "Individual",
                "territory": default_customer_territory,
                'customer_name': oc_customer.name,
                'customer_group': doc_customer_group.get('name'),
                'naming_series': 'CUST-',
                'default_price_list': default_price_list,
                'oc_site': site_name,
                'oc_customer_id': oc_customer.id,
                "oc_sync_from": True,
                "oc_last_sync_from": datetime.now(),
                "oc_sync_to": True,
                "oc_last_sync_to": datetime.now(),
                'oc_firstname': oc_customer.firstname,
                'oc_lastname': oc_customer.lastname,
                'oc_telephone': oc_customer.telephone,
                'oc_fax': oc_customer.fax,
                'oc_email': oc_customer.email,
            }
            doc_customer = frappe.get_doc(params)
            doc_customer.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_customer.get('customer_name'),
                                 doc_customer.get('oc_customer_id'),
                                 doc_customer_group.get('name'),
                                 doc_customer.get_formatted('oc_last_sync_from'),
                                 doc_customer.get('modified')) + extras)
        if add_count > 10:
            break
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results
