from __future__ import unicode_literals
from frappe import _

import frappe

COMMENT_ADDED_FROM_TEMPLATE = '''<span class="text-muted">comment from %s</span>'''


def before_save(doc, method=None):
    if doc.reference_doctype in ("Back Order", "Sales Invoice", "Delivery Note", "Packing Slip"):
        doc_reference = frappe.get_doc(_(doc.reference_doctype), doc.reference_name)
        if frappe.db.exists('Sales Order', doc_reference.get('sales_order')):
            doc_sales_order = frappe.get_doc('Sales Order', doc_reference.get('sales_order'))
            comment = doc.content + COMMENT_ADDED_FROM_TEMPLATE % doc.reference_name
            doc_sales_order.add_comment(doc.communication_medium, text=comment, comment_by=doc.user)
            frappe.clear_cache()
