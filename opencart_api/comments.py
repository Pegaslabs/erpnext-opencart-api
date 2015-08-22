from __future__ import unicode_literals
from frappe import _

import frappe

COMMENT_ADDED_FROM_TEMPLATE = '''<br><small class="text-muted"><span>comment from %s</span></small>'''


def before_save(doc, method=None):
    if doc.comment_doctype in ("Back Order", "Sales Invoice", "Delivery Note", "Packing Slip"):
        doc_comment = frappe.get_doc(_(doc.comment_doctype), doc.comment_docname)
        if frappe.db.exists('Sales Order', doc_comment.get('sales_order')):
            doc_sales_order = frappe.get_doc('Sales Order', doc_comment.get('sales_order'))
            comment = doc.comment + COMMENT_ADDED_FROM_TEMPLATE % doc.comment_docname
            doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by)
            frappe.clear_cache()
