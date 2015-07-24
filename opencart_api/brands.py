from __future__ import unicode_literals

import frappe


def get_brand(manufacturer):
    db_brand = frappe.db.get('Brand', {'name': manufacturer})
    if db_brand:
        return frappe.get_doc('Brand', db_brand.get('name'))


def create_or_update(site_name, oc_manufacturer):
    doc_brand = get_brand(oc_manufacturer.get('name'))
    if doc_brand:
        return doc_brand
        # update existed Brand
        # params = {
        #     'brand': oc_manufacturer.get('name'),
        #     'description': oc_manufacturer.get('name')
        # }
        # doc_brand.update(params)
        # doc_brand.save()
    else:
        # create new Brand
        params = {
            'doctype': 'Brand',
            'brand': oc_manufacturer.get('name'),
            'description': oc_manufacturer.get('name')
        }
        doc_brand = frappe.get_doc(params)
        doc_brand.insert(ignore_permissions=True)
        return doc_brand
