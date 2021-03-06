from __future__ import unicode_literals

import frappe


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
