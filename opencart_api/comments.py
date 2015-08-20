from __future__ import unicode_literals
from frappe import _

import frappe


def before_save(doc, method=None):
    if doc.comment_doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
        doc_comment_name = frappe.get_doc(_(doc.comment_doctype), doc.comment_docname)
        doc_sales_order = frappe.get_doc('Sales Order', doc_comment_name.get('sales_order'))
        doc_sales_order.add_comment(doc.comment_type, text=doc.comment + ' ' + doc.comment_docname, comment_by=doc.comment_by)
