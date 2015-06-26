from __future__ import unicode_literals

import frappe


def get_by_name(site_name, price_list_name):
    db_price_list = frappe.db.get('Price List', {'name': price_list_name})
    if db_price_list:
        return frappe.get_doc('Price List', price_list_name)
