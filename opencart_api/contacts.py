from __future__ import unicode_literals

import frappe


def get_contact(customer, first_name, last_name):
    db_contact = frappe.db.get('Contact', {'customer': customer, 'first_name': first_name, 'last_name': last_name})
    if db_contact:
        return frappe.get_doc('Contact', db_contact.get('name'))


def create_or_update(site_name, oc_customer, doc_customer):
    doc_contact = get_contact(doc_customer.get('name'), oc_customer.get('firstname', ''), oc_customer.get('lastname', ''))
    if doc_contact:
        # update existed Contact
        params = {
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'email_id': oc_customer.get('email', ''),
            'first_name': oc_customer.get('firstname', ''),
            'last_name': oc_customer.get('lastname', ''),
            'customer_name': oc_customer.get('firstname', '') + ' ' + oc_customer.get('lastname', '')
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
            'first_name': oc_customer.get('firstname', ''),
            'last_name': oc_customer.get('lastname', ''),
            'customer_name': oc_customer.get('firstname', '') + ' ' + oc_customer.get('lastname', ''),
            'oc_site': site_name
        }
        doc_contact = frappe.get_doc(params)
        doc_contact.insert(ignore_permissions=True)


def create_or_update_from_guest_order(site_name, doc_customer, oc_order):
    doc_contact = get_contact(doc_customer.get('name'), oc_order.get('firstname', ''), oc_order.get('lastname', ''))
    if doc_contact:
        # update existed Contact
        params = {
            'customer': doc_customer.get('name'),
            'phone': oc_order.get('telephone', ''),
            'email_id': oc_order.get('email', ''),
            'first_name': oc_order.get('firstname', ''),
            'last_name': oc_order.get('lastname', ''),
            'customer_name': oc_order.get('firstname', '') + ' ' + oc_order.get('lastname', '')
        }
        doc_contact.update(params)
        doc_contact.save()
    else:
        # create new Contact
        params = {
            'doctype': 'Contact',
            'customer': doc_customer.get('name'),
            'phone': oc_order.get('telephone', ''),
            'email_id': oc_order.get('email', ''),
            'first_name': oc_order.get('firstname', ''),
            'last_name': oc_order.get('lastname', ''),
            'customer_name': oc_order.get('firstname', '') + ' ' + oc_order.get('lastname', ''),
            'oc_site': site_name
        }
        doc_contact = frappe.get_doc(params)
        doc_contact.insert(ignore_permissions=True)
