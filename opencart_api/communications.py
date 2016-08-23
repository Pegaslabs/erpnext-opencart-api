from __future__ import unicode_literals
from frappe import _

import frappe
from frappe.utils import cstr


COMMENT_ADDED_FROM_TEMPLATE = '''&nbsp<small class="text-muted"><span>comment from %s</span></small>'''


def before_save(doc, method=None):
    if not doc.is_origin_comment or doc.reference_doctype not in ('Sales Order', 'Sales Invoice', 'Packing Slip', 'Delivery Note'):
        return
    if doc.reference_doctype in ("Sales Order", "Sales Invoice", "Delivery Note", "Packing Slip"):
        doc_comment = frappe.get_doc(_(doc.reference_doctype), doc.reference_name)
        if not doc.content:
            return
        comment = cstr(doc.content) + COMMENT_ADDED_FROM_TEMPLATE % doc.reference_name
        if not doc_comment.get('sales_order'):
            if doc.reference_doctype == "Sales Order":
                for doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
                    all_doctypes = frappe.get_all(doctype, filters={'sales_order': doc_comment.name})
                    for i in all_doctypes:
                        doc_reference = frappe.get_doc(doctype, i)
                        doc_reference.add_comment("Info", text=comment, comment_by=doc.user, is_origin_comment=0)
                    frappe.clear_cache(doctype=doctype)
        else:
            if frappe.db.exists('Sales Order', doc_comment.get('sales_order')):
                doc_sales_order = frappe.get_doc('Sales Order', doc_comment.get('sales_order'))
                doc_sales_order.add_comment("Info", text=comment, comment_by=doc.user, is_origin_comment=0)
                frappe.clear_cache(doctype="Sales Order")
                for doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
                    all_doctypes = frappe.get_all(doctype, filters={'sales_order': doc_comment.get('sales_order')})
                    for i in all_doctypes:
                        if i.get('name') != doc_comment.name:
                            doc_comment_new = frappe.get_doc(doctype, i)
                            doc_comment_new.add_comment("Info", text=comment, comment_by=doc.user, is_origin_comment=0)
                    frappe.clear_cache(doctype=doctype)
