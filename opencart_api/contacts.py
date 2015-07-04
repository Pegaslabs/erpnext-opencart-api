from __future__ import unicode_literals

import frappe
from frappe.utils import cstr


def get_contact(site_name, oc_contact_id):
    db_contact = frappe.db.get('Contact', {'oc_site': site_name, 'oc_contact_id': oc_contact_id})
    if db_contact:
        return frappe.get_doc('Contact', db_contact.get('name'))


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

    # contact_id is the same as address_id
    oc_contact_id = oc_address.get('address_id')
    doc_contact = get_contact(site_name, oc_contact_id)

    if not oc_address.get('firstname'):
        frappe.msgprint('First name is missed in Address of Customer %s %s' % (doc_customer.get('name'), doc_customer.get('customer_name')))
        return

    if doc_contact:
        # update existed Contact
        params = {
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'email_id': oc_customer.get('email', ''),
            'first_name': oc_address.get('firstname', ''),
            'last_name': oc_address.get('lastname', ''),
            'customer_name': oc_address.get('lastname', '') + ' ' + oc_address.get('lastname', '')
        }
        doc_contact.update(params)
        doc_contact.save()
    else:
        # create new Contact
        params = {
            'doctype': 'Contact',
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'email_id': oc_customer.get('email', ''),
            'first_name': oc_address.get('firstname', ''),
            'last_name': oc_address.get('lastname', ''),
            'customer_name': oc_address.get('lastname', '') + ' ' + oc_address.get('lastname', ''),
            'oc_site': site_name,
            'oc_contact_id': oc_contact_id,
        }
        doc_contact = frappe.get_doc(params)
        doc_contact.insert(ignore_permissions=True)
