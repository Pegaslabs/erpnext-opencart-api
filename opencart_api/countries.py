from __future__ import unicode_literals

import frappe


def create_if_does_not_exist(country):
    if not country:
        return
    db_country = frappe.db.get('Country', country)
    if not db_country:
        params = {
            'doctype': 'Country',
            'country_name': country
        }
        doc_country = frappe.get_doc(params)
        doc_country.insert(ignore_permissions=True)
