from __future__ import unicode_literals
from frappe import _

import frappe

COMMENT_ADDED_FROM_TEMPLATE = '''<br><small class="text-muted"><span>comment from %s</span></small>'''


def before_save(doc, method=None):
    doc_comment = frappe.get_doc(_(doc.comment_doctype), doc.comment_docname)
    comment = doc.comment + COMMENT_ADDED_FROM_TEMPLATE % doc.comment_docname
    if doc.comment_doctype == 'Sales Order' and doc.is_origin_comment:
        ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.name})
        for i in ps:
            doc_packing_slip = frappe.get_doc('Packing Slip', i)
            doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.name})
        for i in dn:
            doc_delivery_note = frappe.get_doc('Delivery Note', i)
            doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.name})
        for i in si:
            doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
            doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        frappe.clear_cache(doctype='Sales Order')

    elif doc.comment_doctype == 'Packing Slip' and doc_comment.sales_order and doc.is_origin_comment:
        si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.sales_order})
        for i in si:
            doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
            doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by,is_origin_comment=0)
        dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.sales_order})
        for i in dn:
            doc_delivery_note = frappe.get_doc('Delivery Note', i)
            doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
        doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        frappe.clear_cache(doctype='Packing Slip')

    elif doc.comment_doctype == 'Sales Invoice' and doc_comment.sales_order and doc.is_origin_comment:
        ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.sales_order})
        for i in ps:
            doc_packing_slip = frappe.get_doc('Packing Slip', i)
            doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.sales_order})
        for i in dn:
            doc_delivery_note = frappe.get_doc('Delivery Note', i)
            doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
        doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        frappe.clear_cache(doctype='Sales Invoice')

    elif doc.comment_doctype == 'Delivery Note' and doc_comment.sales_order and doc.is_origin_comment:
        ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.sales_order})
        for i in ps:
            doc_packing_slip = frappe.get_doc('Packing Slip', i)
            doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.sales_order})
        for i in si:
            doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
            doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by,is_origin_comment=0)
        doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
        doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
        frappe.clear_cache(doctype='Delivery Note')
