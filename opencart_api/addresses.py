from __future__ import unicode_literals

import frappe
from frappe.utils import cstr

import countries


def get_address(site_name, oc_address_id):
    db_address = frappe.db.get('Address', {'oc_site': site_name, 'oc_address_id': oc_address_id})
    if db_address:
        return frappe.get_doc('Address', db_address.get('name'))


def get_address_by_customer(customer, address_type):
    db_address = frappe.db.get('Address', {'customer': customer, 'address_type': address_type})
    if db_address:
        return frappe.get_doc('Address', db_address.get('name'))


def get_payment_customer_name(oc_order):
    return cstr(oc_order.get('payment_firstname')) + ' ' + cstr(oc_order.get('payment_lastname')).strip()


def get_shipping_customer_name(oc_order):
    return cstr(oc_order.get('shipping_firstname')) + ' ' + cstr(oc_order.get('shipping_lastname')).strip()


def get_address_by_oc_order(customer, oc_order, address_type='Shipping'):
    address_filter = {
        'customer': customer,
        'address_type': address_type,
        'phone': cstr(oc_order.get('telephone')),
        'fax': cstr(oc_order.get('fax')),
        'email_id': cstr(oc_order.get('email')),
        'customer_name': get_payment_customer_name(oc_order),
        'first_name': oc_order.get('payment_firstname'),
        'last_name': oc_order.get('payment_lastname'),
        'pincode': cstr(oc_order.get('payment_postcode')),
        'country': cstr(oc_order.get('payment_country')),
        'state': cstr(oc_order.get('payment_zone')),
        'city': cstr(oc_order.get('payment_city')),
        'address_line1': cstr(oc_order.get('payment_address_1')),
        'address_line2': cstr(oc_order.get('payment_address_2'))
    }
    if address_type == 'Shipping':
        if (oc_order.get('shipping_postcode') and oc_order.get('shipping_country') and
            oc_order.get('shipping_zone') and oc_order.get('shipping_city') and
            oc_order.get('shipping_address_1')):
            address_filter = {
                'customer': customer,
                'address_type': address_type,
                'phone': cstr(oc_order.get('telephone')),
                'fax': cstr(oc_order.get('fax')),
                'email_id': cstr(oc_order.get('email')),
                'customer_name': get_shipping_customer_name(oc_order),
                'first_name': oc_order.get('shipping_firstname'),
                'last_name': oc_order.get('shipping_lastname'),
                'pincode': cstr(oc_order.get('shipping_postcode')),
                'country': cstr(oc_order.get('shipping_country')),
                'state': cstr(oc_order.get('shipping_zone')),
                'city': cstr(oc_order.get('shipping_city')),
                'address_line1': cstr(oc_order.get('shipping_address_1')),
                'address_line2': cstr(oc_order.get('shipping_address_2'))
            }
    db_addresses = frappe.db.sql("""select name
        from `tabAddress`
        where ifnull(customer, '')=%(customer)s and
        ifnull(address_type, '')=%(address_type)s and
        ifnull(phone, '')=%(phone)s and
        ifnull(fax, '')=%(fax)s and
        ifnull(email_id, '')=%(email_id)s and
        ifnull(customer_name, '') like %(customer_name)s and
        (ifnull(first_name, '')='' or ifnull(first_name, '')=%(first_name)s) and
        (ifnull(last_name, '')='' or ifnull(last_name, '')=%(last_name)s) and
        ifnull(pincode, '')=%(pincode)s and
        ifnull(country, '')=%(country)s and
        ifnull(state, '')=%(state)s and
        ifnull(city, '')=%(city)s and
        ifnull(address_line1, '')=%(address_line1)s and
        ifnull(address_line2, '')=%(address_line2)s""", address_filter, as_dict=1)

    if db_addresses:
        return frappe.get_doc('Address', db_addresses[0].get('name'))


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

    if not oc_address.get('country'):
        frappe.msgprint('Warning. Country is missed in Address of Customer %s %s' % (doc_customer.get('name'), doc_customer.get('customer_name')))
        return

    countries.create_if_does_not_exist(oc_address.get('country'))
    first_name = oc_address.get('firstname') or oc_customer.get('firstname') or ''
    last_name = oc_address.get('lastname') or oc_customer.get('lastname') or ''
    customer_name = first_name + ' ' + last_name
    oc_address_id = oc_address.get('address_id')
    # doc_address = get_address(site_name, oc_address_id)
    address_type = 'Office' if oc_address.get('company') else 'Personal'
    doc_address = get_address_by_customer(doc_customer.get('name'), address_type)
    if doc_address:
        # update existed Address (Billing)
        params = {
            'address_type': address_type,
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'fax': oc_customer.get('fax', ''),
            'email_id': oc_customer.get('email', ''),
            'customer_name': customer_name,
            'first_name': first_name,
            'last_name': last_name,
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', ''),
            'address_line2': oc_address.get('address_2', ''),
            'oc_address_id': oc_address_id
        }
        doc_address.update(params)
        doc_address.save()
    else:
        # create new Address
        params = {
            'doctype': 'Address',
            'address_type': address_type,
            'customer': doc_customer.get('name'),
            'phone': oc_customer.get('telephone', ''),
            'fax': oc_customer.get('fax', ''),
            'email_id': oc_customer.get('email', ''),
            'customer_name': customer_name,
            'first_name': first_name,
            'last_name': last_name,
            'pincode': oc_address.get('postcode', ''),
            'country': oc_address.get('country', ''),
            'state': oc_address.get('zone'),
            'city': oc_address.get('city', 'not specified'),
            'address_line1': oc_address.get('address_1', ''),
            'address_line2': oc_address.get('address_2', ''),
            'oc_site': site_name,
            'oc_address_id': oc_address_id
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


def get_from_oc_order(site_name, customer, oc_order, address_type='Shipping'):
    # creating address from order payment
    # billing address
    countries.create_if_does_not_exist(oc_order.get('payment_country'))
    doc_address = get_address_by_oc_order(customer, oc_order, 'Billing')
    ret_doc_address = None
    if not doc_address:
        # create new Address (Billing)
        address_params = {
            'doctype': 'Address',
            'address_type': 'Billing',
            'allow_multiple_addresses': 1,
            # 'is_primary_address': 1,
            'is_shipping_address': 0,
            'customer': customer,
            'phone': cstr(oc_order.get('telephone')),
            'fax': cstr(oc_order.get('fax')),
            'email_id': cstr(oc_order.get('email')),
            'customer_name': get_payment_customer_name(oc_order),
            'first_name': oc_order.get('payment_firstname'),
            'last_name': oc_order.get('payment_lastname'),
            'pincode': cstr(oc_order.get('payment_postcode')),
            'country': cstr(oc_order.get('payment_country')),
            'state': cstr(oc_order.get('payment_zone')),
            'city': cstr(oc_order.get('payment_city')),
            'address_line1': cstr(oc_order.get('payment_address_1')),
            'address_line2': cstr(oc_order.get('payment_address_2')),
            'oc_site': site_name,
        }
        doc_address = frappe.get_doc(address_params)
        doc_address.autoname()
        doc_address.insert(ignore_permissions=True)
    if address_type == 'Billing':
        ret_doc_address = doc_address
        if not ret_doc_address.first_name or not ret_doc_address.last_name:
            ret_doc_address.first_name = oc_order.get('payment_firstname')
            ret_doc_address.last_name = oc_order.get('payment_lastname')
            ret_doc_address.save()

    # shipping address
    shipping_country = oc_order.get('shipping_country') or oc_order.get('payment_country')
    countries.create_if_does_not_exist(shipping_country)
    doc_address = get_address_by_oc_order(customer, oc_order, 'Shipping')
    if not doc_address:
        if not (oc_order.get('shipping_postcode') and oc_order.get('shipping_country') and
            oc_order.get('shipping_zone') and oc_order.get('shipping_city') and oc_order.get('shipping_address_1')):
            address_params = {
                'doctype': 'Address',
                'address_type': 'Shipping',
                'allow_multiple_addresses': 1,
                'is_primary_address': 0,
                'is_shipping_address': 1,
                'customer': customer,
                'phone': cstr(oc_order.get('telephone')),
                'fax': cstr(oc_order.get('fax')),
                'email_id': cstr(oc_order.get('email')),
                'customer_name': get_payment_customer_name(oc_order),
                'first_name': oc_order.get('payment_firstname'),
                'last_name': oc_order.get('payment_lastname'),
                'pincode': cstr(oc_order.get('payment_postcode')),
                'country': cstr(oc_order.get('payment_country')),
                'state': cstr(oc_order.get('payment_zone')),
                'city': cstr(oc_order.get('payment_city')),
                'address_line1': cstr(oc_order.get('payment_address_1')),
                'address_line2': cstr(oc_order.get('payment_address_2')),
                'oc_site': site_name,
            }
        else:
            address_params = {
                'doctype': 'Address',
                'address_type': 'Shipping',
                'allow_multiple_addresses': 1,
                'is_primary_address': 0,
                'is_shipping_address': 1,
                'customer': customer,
                'phone': cstr(oc_order.get('telephone')),
                'fax': cstr(oc_order.get('fax')),
                'email_id': cstr(oc_order.get('email')),
                'customer_name': get_shipping_customer_name(oc_order),
                'first_name': oc_order.get('shipping_firstname'),
                'last_name': oc_order.get('shipping_lastname'),
                'pincode': cstr(oc_order.get('shipping_postcode')),
                'country': cstr(oc_order.get('shipping_country')),
                'state': cstr(oc_order.get('shipping_zone')),
                'city': cstr(oc_order.get('shipping_city')),
                'address_line1': cstr(oc_order.get('shipping_address_1')),
                'address_line2': cstr(oc_order.get('shipping_address_2')),
                'oc_site': site_name,
            }
        # create new Address (Shipping)
        doc_address = frappe.get_doc(address_params)
        doc_address.autoname()
        doc_address.insert(ignore_permissions=True)
    if address_type == 'Shipping':
        ret_doc_address = doc_address
        if not ret_doc_address.first_name or not ret_doc_address.last_name:
            ret_doc_address.first_name = oc_order.get('shipping_firstname')
            ret_doc_address.last_name = oc_order.get('shipping_lastname')
            ret_doc_address.save()

    return ret_doc_address
