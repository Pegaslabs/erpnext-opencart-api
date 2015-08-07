from __future__ import unicode_literals

import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_packing_slip(source_name, target_doc=None):
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
