from __future__ import unicode_literals
from datetime import datetime
import uuid

import frappe
from frappe.utils import cstr

import customer_groups
import territories
import oc_api
import oc_stores
from decorators import sync_to_opencart


OC_MANDATORY_FIELDS = ('firstname', 'lastname', 'email', 'telephone')


@sync_to_opencart
def oc_validate(doc, method=None):
    site_name = doc.get('oc_site')
    customer_group_name = doc.get('customer_group')
    valid_customer_group_names = [customer_group.get('name') for customer_group in customer_groups.get_all_by_oc_site(site_name) if customer_group.get('oc_customer_group_id')]
    if customer_group_name not in valid_customer_group_names:
        frappe.throw('To sync Customer to Opencart Site, Customer Group must be one of the following:\n%s' % cstr(', '.join(valid_customer_group_names)))
    doc_customer_group = frappe.get_doc('Customer Group', customer_group_name)
    doc.oc_firstname = doc.get('customer_name').strip().split()[0]
    doc.oc_lastname = ' '.join(doc.get('customer_name').strip().split()[1:])
    data = {
        'firstname': doc.oc_firstname,
        'lastname': doc.oc_lastname,
        'email': doc.get('oc_email'),
        'telephone': doc.get('oc_telephone'),
        'fax': doc.get('oc_fax'),
        'status': doc.get('oc_status'),
        'customer_group_id': doc_customer_group.get('oc_customer_group_id')
        # 'custom_field': {
        #         'account': {
        #             '1': '6666555777',
        #             '2': '1'
        #         }
        # },
        # 'address': [
        #     {
        #         'firstname': 'firstname',
        #         'lastname': 'lastname',
        #         'company': 'companyname',
        #         'address_1': 'address_1',
        #         'address_2': 'address_2',
        #         'city': 'cit',
        #         'country_id': '1',
        #         'zone_id': '1',
        #         'postcode': '3333',
        #         'country': 'india',
        #         'default': '1'
        #     },
        #     {
        #         'firstname': 'firstname',
        #         'lastname': 'lastname',
        #         'company': 'companyname',
        #         'address_1': 'address_1',
        #         'address_2': 'address_2',
        #         'city': 'city',
        #         'country_id': '1',
        #         'zone_id': '1',
        #         'postcode': '3333',
        #         'country': 'india'
        #     }
        # ]
    }

    # updating or creating customer
    oc_customer_id = doc.get('oc_customer_id')
    get_customer_success, oc_customer = False, {}
    if oc_customer_id:
        get_customer_success, oc_customer = oc_api.get(site_name).get_customer(oc_customer_id)

    if get_customer_success:
        # update existed customer on Opencart site
        success, resp = oc_api.get(site_name).update_customer(oc_customer_id, data)
        if success:
            frappe.msgprint('Customer is updated successfully on Opencart site')
            doc.update({'oc_last_sync_to': datetime.now()})
        else:
            frappe.msgprint('Customer is not updated on Opencart site.\nError: %s' % resp.get('error') or 'Unknown')
    else:
        # add new customer on Opencart site
        random_password = uuid.uuid4().hex[:20]
        data.update({
            'password': random_password,
            'confirm': random_password,
            'approved': '1',
            'safe': '1',
            'newsletter': '0'
        })
        success, resp = oc_api.get(site_name).create_customer(data)
        if success:
            doc.update({
                'oc_customer_id': resp.get('data', {}).get('id', ''),
                'oc_last_sync_to': datetime.now()
            })
            frappe.msgprint('Customer is created successfully on Opencart site')
        else:
            frappe.msgprint('Customer is not created on Opencart site.\nError: %s' % resp.get('error') or 'Unknown')


@sync_to_opencart
def oc_delete(doc, method=None):
    site_name = doc.get('oc_site')
    oc_customer_id = doc.get('oc_customer_id')
    success, resp = oc_api.get(site_name).delete_customer(oc_customer_id)
    if success:
        frappe.msgprint('Customer was deleted successfully on Opencart site')
    else:
        frappe.throw('Customer is not deleted on Opencart site. Error: %s' % resp.get('error', 'Unknown'))


def get_customer(site_name, oc_customer_id):
    db_customer = frappe.db.get('Customer', {'oc_site': site_name, 'oc_customer_id': oc_customer_id})
    if db_customer:
        return frappe.get_doc('Customer', db_customer.get('name'))


def get_guest_customer(site_name, email, first_name, last_name):
    db_customer = frappe.db.get('Customer', {'oc_site': site_name, 'oc_email': email, 'oc_firstname': first_name, 'oc_lastname': last_name})
    if db_customer:
        return frappe.get_doc('Customer', db_customer.get('name'))


def get_customer_group(site_name, oc_customer_id, doc_customer=None):
    if doc_customer:
        return frappe.get_doc('Customer Group', doc_customer.get('customer_group'))
    else:
        db_customer = frappe.db.get('Customer', {'oc_site': site_name, 'oc_customer_id': oc_customer_id})
        if db_customer:
            doc_customer = frappe.get_doc('Customer', db_customer.get('name'))
            return frappe.get_doc('Customer Group', doc_customer.get('customer_group'))


def get_customer_group_id(site_name, oc_customer_id, doc_customer=None):
    doc_customer_group = get_customer_group(site_name, oc_customer_id, doc_customer)
    if doc_customer_group:
        return doc_customer_group.get('oc_customer_group_id')


def make_full_name(first_name, last_name):
    return first_name + ' ' + last_name


def create_guest_from_order(site_name, oc_order):
    doc_store = oc_stores.get(site_name, oc_order.get('store_id'))
    if doc_store:
        customer_group_name = doc_store.get('oc_customer_group')
        if customer_group_name:
            doc_customer_group = frappe.get_doc('Customer Group', customer_group_name)
            default_price_list = doc_customer_group.get('default_price_list')
            territory_name = territories.get_by_iso_code3(oc_order.get('shipping_iso_code_3'), oc_order.get('shipping_zone_code'))
            # create new Customer
            params = {
                'doctype': 'Customer',
                'customer_type': 'Individual',
                'territory': territory_name,
                'customer_name': make_full_name(oc_order.get('firstname'), oc_order.get('lastname')),
                'customer_group': doc_customer_group.get('name'),
                'naming_series': 'CUST-',
                'default_price_list': default_price_list,
                'oc_guest': 1,
                'oc_is_updating': 1,
                'oc_site': site_name,
                'oc_customer_id': oc_order.get('customer_id'),
                'oc_status': 1,
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': True,
                'oc_last_sync_to': datetime.now(),
                'oc_firstname': oc_order.get('firstname'),
                'oc_lastname': oc_order.get('lastname'),
                'oc_telephone': oc_order.get('telephone'),
                'oc_fax': oc_order.get('fax'),
                'oc_email': oc_order.get('email')
            }
            doc_customer = frappe.get_doc(params)
            doc_customer.insert(ignore_permissions=True)
            return doc_customer
        else:
            frappe.throw('Customer Group is not set in Opencart Store "%s"' % doc_store.get('name'))
    else:
        frappe.throw('Opencart Store with store_id "%s" does not exist' % oc_order.get('store_id'))


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

    site_doc = frappe.get_doc('Opencart Site', site_name)
    # root_customer_group = site_doc.get('root_customer_group')
    default_customer_territory = site_doc.get('default_customer_territory') or 'All Territories'
    doc_customer_groups_cache = {}
    for success, oc_customer in oc_api.get(site_name).get_customers():
        check_count += 1

        oc_customer_name = make_full_name(oc_customer.get('firstname'), oc_customer.get('lastname'))
        customer_id = oc_customer.get('customer_id')

        # validation
        # missed_mandatory_fields = [field for field in OC_MANDATORY_FIELDS if not oc_customer.get(field)]
        # if missed_mandatory_fields:
        #     skip_count += 1
        #     extras = (1, 'skipped', 'Skipped: mandatory fileds missed: %s' % ', '.join(missed_mandatory_fields))
        #     results_list.append((oc_customer_name, customer_id, '', '', '') + extras)
        #     continue

        doc_customer_group = doc_customer_groups_cache.get(oc_customer.get('customer_group_id'))
        if not doc_customer_group:
            doc_customer_group = customer_groups.get(site_name, oc_customer.get('customer_group_id'))
            doc_customer_groups_cache[oc_customer.get('customer_group_id')] = doc_customer_group

        if not doc_customer_group:
            skip_count += 1
            extras = (1, 'skipped', 'Skipped: parent group missed')
            results_list.append((oc_customer_name, customer_id, '', '', '') + extras)
            continue

        doc_customer = get_customer(site_name, customer_id)
        if doc_customer:
            # update existed Customer
            # check here for a need to update Customer
            params = {
                'customer_name': oc_customer_name,
                'customer_group': doc_customer_group.get('name'),
                'oc_last_sync_from': datetime.now(),
                'oc_is_updating': 1,
                'oc_status': 1,
                'oc_firstname': oc_customer.get('firstname'),
                'oc_lastname': oc_customer.get('lastname'),
                'oc_telephone': oc_customer.get('telephone'),
                'oc_fax': oc_customer.get('fax'),
                'oc_email': oc_customer.get('email'),
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
            # if not default_price_list:
            #     skip_count += 1
            #     extras = (1, 'skipped', 'Skipped: missed default price list in customer group')
            #     results_list.append((oc_customer_name, customer_id, '', '', '') + extras)
            #     continue

            # create new Customer
            params = {
                'doctype': 'Customer',
                'customer_type': 'Individual',
                'territory': default_customer_territory,
                'customer_name': oc_customer_name,
                'customer_group': doc_customer_group.get('name'),
                'naming_series': 'CUST-',
                'default_price_list': default_price_list,
                'oc_is_updating': 1,
                'oc_site': site_name,
                'oc_customer_id': customer_id,
                'oc_status': 1,
                'oc_sync_from': True,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': True,
                'oc_last_sync_to': datetime.now(),
                'oc_firstname': oc_customer.get('firstname'),
                'oc_lastname': oc_customer.get('lastname'),
                'oc_telephone': oc_customer.get('telephone'),
                'oc_fax': oc_customer.get('fax'),
                'oc_email': oc_customer.get('email')
            }
            doc_customer = frappe.get_doc(params)
            if not doc_customer.get('customer_name'):
                continue
            doc_customer.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_customer.get('customer_name'),
                                 doc_customer.get('oc_customer_id'),
                                 doc_customer_group.get('name'),
                                 doc_customer.get_formatted('oc_last_sync_from'),
                                 doc_customer.get('modified')) + extras)
    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results
