from __future__ import unicode_literals
from frappe import _

import frappe

COMMENT_ADDED_FROM_TEMPLATE = '''<span class="text-muted">comment from %s</span>'''


def before_save(doc, method=None):
    pass
    # if doc.reference_doctype in ("Sales Order", "Sales Invoice", "Delivery Note", "Packing Slip"):
    #     doc_comment = frappe.get_doc(_(doc.reference_doctype), doc.reference_name)
    #     comment = doc.content + COMMENT_ADDED_FROM_TEMPLATE % doc.reference_name
    #     if not doc_comment.get('sales_order'):
    #         if doc.reference_doctype == "Sales Order":
    #             for doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
    #                 all_doctypes = frappe.get_all(doctype, filters={'sales_order': doc_comment.name})
    #                 for i in all_doctypes:
    #                     doc_reference = frappe.get_doc(doctype, i)
    #                     doc_reference.add_comment(doc.communication_medium, text=comment, comment_by=doc.user, is_origin_comment=0)
    #                 frappe.clear_cache(doctype=doctype)
    #     else:
    #         if frappe.db.exists('Sales Order', doc_comment.get('sales_order')):
    #             doc_sales_order = frappe.get_doc('Sales Order', doc_comment.get('sales_order'))
    #             doc_sales_order.add_comment(doc.communication_medium, text=comment, comment_by=doc.user, is_origin_comment=0)
    #             frappe.clear_cache(doctype="Sales Order")
    #             for doctype in ("Sales Invoice", "Delivery Note", "Packing Slip"):
    #                 all_doctypes = frappe.get_all(doctype, filters={'sales_order': doc_comment.get('sales_order')})
    #                 for i in all_doctypes:
    #                     if i.get('name') != doc_comment.name:
    #                         doc_comment_new = frappe.get_doc(doctype, i)
    #                         doc_comment_new.add_comment(doc.communication_medium, text=comment, comment_by=doc.user, is_origin_comment=0)
    #                 frappe.clear_cache(doctype=doctype)
    ##################################################################################################
    # if not (doc.comment_doctype in ('Sales Order', 'Sales Invoice', 'Packing Slip', 'Delivery Note') and doc.is_origin_comment):
    #     return
    # doc_comment = frappe.get_doc(_(doc.comment_doctype), doc.comment_docname)
    # comment = doc.comment + COMMENT_ADDED_FROM_TEMPLATE % doc.comment_docname
    # if doc.comment_doctype == 'Sales Order':
    #     ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.name})
    #     for i in ps:
    #         doc_packing_slip = frappe.get_doc('Packing Slip', i)
    #         doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.name})
    #     for i in dn:
    #         doc_delivery_note = frappe.get_doc('Delivery Note', i)
    #         doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.name})
    #     for i in si:
    #         doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
    #         doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     frappe.clear_cache(doctype='Sales Order')

    # elif doc.comment_doctype == 'Packing Slip' and doc_comment.sales_order:
    #     si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.sales_order})
    #     for i in si:
    #         doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
    #         doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.sales_order})
    #     for i in dn:
    #         doc_delivery_note = frappe.get_doc('Delivery Note', i)
    #         doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
    #     doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     frappe.clear_cache(doctype='Packing Slip')

    # elif doc.comment_doctype == 'Sales Invoice' and doc_comment.sales_order:
    #     ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.sales_order})
    #     for i in ps:
    #         doc_packing_slip = frappe.get_doc('Packing Slip', i)
    #         doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     dn = frappe.get_all('Delivery Note', filters={'sales_order': doc_comment.sales_order})
    #     for i in dn:
    #         doc_delivery_note = frappe.get_doc('Delivery Note', i)
    #         doc_delivery_note.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
    #     doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     frappe.clear_cache(doctype='Sales Invoice')

    # elif doc.comment_doctype == 'Delivery Note' and doc_comment.sales_order:
    #     ps = frappe.get_all('Packing Slip', filters={'sales_order': doc_comment.sales_order})
    #     for i in ps:
    #         doc_packing_slip = frappe.get_doc('Packing Slip', i)
    #         doc_packing_slip.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     si = frappe.get_all('Sales Invoice', filters={'sales_order': doc_comment.sales_order})
    #     for i in si:
    #         doc_sales_invoice = frappe.get_doc('Sales Invoice', i)
    #         doc_sales_invoice.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     doc_sales_order = frappe.get_doc('Sales Order', doc_comment.sales_order)
    #     doc_sales_order.add_comment(doc.comment_type, text=comment, comment_by=doc.comment_by, is_origin_comment=0)
    #     frappe.clear_cache(doctype='Delivery Note')
