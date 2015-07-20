from __future__ import unicode_literals

import frappe
from frappe.utils import cstr

import countries


def get_address(site_name, oc_address_id):
    db_address = frappe.db.get('Address', {'oc_site': site_name, 'oc_address_id': oc_address_id})
    if db_address:
        return frappe.get_doc('Address', db_address.get('name'))


def get_address_by_customer(customer, customer_name):
    db_address = frappe.db.get('Address', {'customer': customer, 'customer_name': customer_name})
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

    countries.create_if_does_not_exist(oc_address.get('country'))
    firstname = oc_address.get('firstname') or oc_customer.get('firstname') or ''
    lastname = oc_address.get('lastname') or oc_customer.get('lastname') or ''
    customer_name = firstname + ' ' + lastname

    if doc_address:
        # update existed Address
        params = {
            'address_type': 'Billing',
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'fax': oc_customer.get('fax', ''),
            'email_id': oc_customer.get('email', ''),
            'customer_name': customer_name,
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', ''),
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
            'customer_name': customer_name,
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', ''),
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


def create_or_update_from_order(site_name, doc_customer, oc_order):
    # creating address from order payment
    if not oc_order.get('shipping_country'):
        frappe.msgprint('Warning. Country is missed in Address of Customer %s %s' % (doc_customer.get('name'), doc_customer.get('customer_name')))
        return
    countries.create_if_does_not_exist(oc_order.get('shipping_country'))
    firstname = oc_order.get('shipping_firstname', '')
    lastname = oc_order.get('shipping_lastname', '')
    customer_name = firstname + ' ' + lastname

    doc_address = get_address_by_customer(doc_customer.get('name'), customer_name)
    if doc_address:
        # update existed Address
        params = {
            'phone': oc_order.get('telephone', ''),
            'fax': oc_order.get('fax', ''),
            'email_id': oc_order.get('email', ''),
            'customer_name': customer_name,
            'pincode': oc_order.get('shipping_postcode', ''),
            'country': oc_order.get('shipping_country', ''),
            'state': oc_order.get('shipping_zone'),
            'city': oc_order.get('shipping_city', ''),
            'address_line1': oc_order.get('shipping_address_1', ''),
            'address_line2': oc_order.get('shipping_address_2', '')
        }
        doc_address.update(params)
        doc_address.save()
    else:
        # create new Address
        params = {
            'doctype': 'Address',
            'address_type': 'Billing',
            'customer': doc_customer.get('name'),
            'phone': oc_order.get('telephone', ''),
            'fax': oc_order.get('fax', ''),
            'email_id': oc_order.get('email', ''),
            'customer_name': customer_name,
            'pincode': oc_order.get('shipping_postcode', ''),
            'country': oc_order.get('shipping_country', ''),
            'state': oc_order.get('shipping_zone'),
            'city': oc_order.get('shipping_city', ''),
            'address_line1': oc_order.get('shipping_address_1', ''),
            'address_line2': oc_order.get('shipping_address_2', ''),
            'oc_site': site_name,
        }
        doc_address = frappe.get_doc(params)
        doc_address.insert(ignore_permissions=True)
