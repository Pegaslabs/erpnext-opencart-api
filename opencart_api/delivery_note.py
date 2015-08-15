from __future__ import unicode_literals

import frappe
from frappe.model.mapper import get_mapped_doc


def validate(doc, method=None):
    pass
    # db_packing_slip_docstatus = frappe.db.get_value('Packing Slip', {'delivery_note': doc.sales_order}, 'docstatus')
    # if db_packing_slip_docstatus is not None and db_packing_slip_docstatus != 2:
    #     frappe.throw('Cannot make new Packing Slip: Packing Slip is already created and its docstatus is not canceled.')

    # db_delivery_note = frappe.db.get_value('Delivery Note', {'sales_order': doc.sales_order}, ['name', 'docstatus'], as_dict=True)
    # if db_delivery_note is not None and db_delivery_note.get('docstatus') != 2:
    #     frappe.throw('Cannot make new Delivery Note: Sales Order has already Delivery Note %s created and its docstatus is not canceled.' % db_delivery_note.get('name'))


def before_submit(self, method=None):
    if not self.oc_tracking_number:
        frappe.throw('Please submit at first the Packing Slip.\nTracking number is missed in this Delivery Note document.')


@frappe.whitelist()
def make_packing_slip(source_name, target_doc=None):

    db_packing_slip_docstatus = frappe.db.get_value('Packing Slip', {'delivery_note': source_name}, 'docstatus')
    if db_packing_slip_docstatus is not None and db_packing_slip_docstatus != 2:
        frappe.throw('Cannot make new Packing Slip: Packing Slip is already created and its docstatus is not canceled.')

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Packing Slip",
            "field_map": {
                "name": "delivery_note",
                "letter_head": "letter_head"
            },
            "validation": {
                "docstatus": ["=", 0]
            }
        }
    }, target_doc)

    return doclist


def on_delivery_note_added(delivery_note):
    pass
    # ps = make_packing_slip(delivery_note)
    # ps.get_items()
    # ps.insert()
