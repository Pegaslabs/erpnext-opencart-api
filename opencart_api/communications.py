from __future__ import unicode_literals
from frappe import _

import frappe


def before_save(doc, method=None):
    if doc.reference_doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
        doc_reference_name = frappe.get_doc(_(doc.reference_doctype), doc.reference_name)
        doc_sales_order = frappe.get_doc('Sales Order', doc_reference_name.get('sales_order'))
        doc_sales_order.add_comment(doc.communication_medium, text=doc.content + doc.reference_name, comment_by=doc.user)
