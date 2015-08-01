from __future__ import unicode_literals

import frappe


def initialize():
    # update Delivery Note status options
    status_options = '\nDraft\nSubmitted\nCancelled\nReady to ship'
    df = frappe.get_doc('DocField', {'parent': 'Delivery Note', 'fieldname': 'status'})
    if status_options != df.get('options'):
        df.update({'options': status_options})
        df.save()

initialize()
frappe.db.commit()
