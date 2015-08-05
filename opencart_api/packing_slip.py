from __future__ import unicode_literals

import frappe

from erpnext.accounts.doctype.packing_slip.packing_slip import PackingSlip

from bins import get_bin_location


def validate(doc, method=None):
    # update tracking number from packing slip to delivery note
    if frappe.db.get_value('Delivery Note', doc.get('delivery_note'), 'oc_tracking_number') != doc.get('oc_tracking_number'):
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'oc_tracking_number', doc.get('oc_tracking_number'))


def on_submit(doc, method=None):
    dn = frappe.get_doc('Delivery Note', doc.get('delivery_note'))
    # packing_slips = frappe.get_all('Packing Slip', fields=['name', 'docstatus'], filters={'delivery_note': doc.get('delivery_note')})
    # if dn.get('docstatus') == 0 and packing_slips and all(map(lambda ps: ps.docstatus == 1, packing_slips)):
    if dn.get('docstatus') == 0:  # "Draft" or "Ready to ship"
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'status', 'Ready to ship')


def on_cancel(doc, method=None):
    dn = frappe.get_doc('Delivery Note', doc.get('delivery_note'))
    if dn.get('docstatus') == 0:  # "Draft" or "Ready to ship"
        frappe.db.set_value('Delivery Note', doc.get('delivery_note'), 'status', 'Draft')
    elif dn.get('docstatus') == 1:  # "Submitted"
        pass
        # dn.cancel()
    elif dn.get('docstatus') == 2:  # "Cancelled":
        pass


def update_item_details(self):
        """
            Fill empty columns in Packing Slip Item
        """
        frappe.msgprint('update_item_details from erpnext')
        if not self.from_case_no:
            self.from_case_no = self.get_recommended_case_no()

        for d in self.get("items"):
            res = frappe.db.get_value("Item", d.item_code, ["net_weight", "weight_uom"], as_dict=True)

            if res and len(res)>0:
                d.net_weight = res["net_weight"]
                d.weight_uom = res["weight_uom"]

            d.warehouse = frappe.db.get_value('Delivery Note Item', {'item_code': d.item_code}, 'warehouse')
            d.bin_location = get_bin_location(d.item_code, d.warehouse)


setattr(PackingSlip, 'update_items_details', update_item_details)
