from __future__ import unicode_literals

import frappe

import oc_api


def get(site_name, oc_product_id, oc_customer_id):
	pass
    # db_opencart_store = frappe.db.get("Opencart Discount", {"oc_site": site_name, "oc_store_id": oc_store_id})
    # if db_opencart_store:
    #     return frappe.get_doc('Opencart Discount', db_opencart_store.get("name"))
