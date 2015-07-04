from __future__ import unicode_literals

import frappe
from frappe.utils import cstr

import countries


def get_address(site_name, oc_address_id):
    db_address = frappe.db.get('Address', {'oc_site': site_name, 'oc_address_id': oc_address_id})
    if db_address:
        return frappe.get_doc('Address', db_address.get('name'))


def create_or_update(site_name, oc_customer, doc_customer):
    oc_addresses = oc_customer.get('addresses', {})
    oc_address = {}
    # gettting first address`
    if isinstance(oc_addresses, list):
        for addr in oc_addresses:
            oc_address = addr
            break
    else:
        for addr_id, addr in oc_addresses.items():
            oc_address = addr
            break
    # no addresses found
    if not oc_address:
        return

    oc_address_id = oc_address.get('address_id')
    doc_address = get_address(site_name, oc_address_id)

    if not oc_address.get('country'):
        frappe.msgprint('Warning. Country is missed in Address of Customer %s %s' % (doc_customer.get('name'), doc_customer.get('customer_name')))
        return

    if not doc_customer.get('telephone'):
        frappe.msgprint('Warning. Telephone is missed in Address of Customer %s %s' % (doc_customer.get('name'), doc_customer.get('customer_name')))
        return

    countries.create_if_does_not_exist(oc_address.get('country'))
    if doc_address:
        # update existed Address
        params = {
            'address_type': 'Billing',
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'fax': oc_customer.get('fax', ''),
            'email_id': oc_customer.get('email', ''),
            'customer_name': oc_address.get('firstname', '') + ' ' + oc_address.get('lastname', ''),
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', 'not specified'),
            'address_line2': oc_address.get('address_2', '')
        }
        doc_address.update(params)
        doc_address.save()
    else:
        # create new Address
        params = {
            'doctype': 'Address',
            'address_type': 'Billing',
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'fax': oc_customer.get('fax', ''),
            'email_id': oc_customer.get('email', ''),
            'customer_name': oc_address.get('firstname', '') + ' ' + oc_address.get('lastname', ''),
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', 'not specified'),
            'address_line2': oc_address.get('address_2', ''),
            'oc_site': site_name,
            'oc_address_id': oc_address_id,
        }
        doc_address = frappe.get_doc(params)
        doc_address.insert(ignore_permissions=True)

    # update Customer's name to Company name if needed
    if oc_address.get('company') and (oc_address.get('company') != doc_customer.get('customer_name') or 'Company' != doc_customer.get('customer_type')):
        doc_customer.update({
            'oc_is_updating': 1,
            'customer_type': 'Company',
            'customer_name': oc_address.get('company')
        })
        doc_customer.save()
