from __future__ import unicode_literals

import frappe


def validate(doc, method=None):
    # update tracking number from packing slip to delivery note
    if frappe.db.get_value('Delivery Note', doc.get('delivery_note'), 'oc_tracking_number') != doc.get('oc_tracking_number'):
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'oc_tracking_number', doc.get('oc_tracking_number'))


def before_submit(doc, method=None):
    if not doc.oc_tracking_number:
        frappe.throw('Packing Slip cannot be submitted with tracking number not set.')


def on_submit(doc, method=None):
    dn = frappe.get_doc('Delivery Note', doc.get('delivery_note'))
    # packing_slips = frappe.get_all('Packing Slip', fields=['name', 'docstatus'], filters={'delivery_note': doc.get('delivery_note')})
    # if dn.get('docstatus') == 0 and packing_slips and all(map(lambda ps: ps.docstatus == 1, packing_slips)):
    if dn.get('docstatus') == 0:  # "Draft" or "Ready to ship"
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'status', 'Ready to ship')
        frappe.clear_cache()


def on_cancel(doc, method=None):
    dn = frappe.get_doc('Delivery Note', doc.get('delivery_note'))
    if dn.get('docstatus') == 0:  # "Draft" or "Ready to ship"
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'status', 'Draft')
    elif dn.get('docstatus') == 1:  # "Submitted"
        pass
        # dn.cancel()
    elif dn.get('docstatus') == 2:  # "Cancelled":
        pass


@frappe.whitelist()
def get_item_by_barcode_or_item_code(barcode, item_code):
    if barcode:
        return frappe.db.get('Item', {'barcode': barcode})
    elif item_code:
        return frappe.db.get('Item', {'item_code': item_code.upper()})
