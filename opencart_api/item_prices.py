from __future__ import unicode_literals

import frappe
import items


def resolve_site_from_item_price(doc_item_price):
    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': doc_item_price.get('price_list')})
    if not db_oc_price_list:
        return
    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
    return db_oc_store.get('oc_site')


def oc_on_update(doc, method=None):
    oc_site = resolve_site_from_item_price(doc)
    doc_item = frappe.get_doc('Item', doc.get('item_code'))
    items.sync_item_to_oc(doc_item, site_name=oc_site)
