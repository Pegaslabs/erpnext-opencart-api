from __future__ import unicode_literals

import frappe
from frappe.utils import cstr
from erpnext.stock.doctype.delivery_note import delivery_note as erpnext_delivery_note
from erpnext.selling.doctype.sales_order import sales_order as erpnext_sales_order


def on_submit(self, method=None):
    sales_order = frappe.db.get_value('Delivery Note', self.name, 'sales_order')
    if not erpnext_sales_order.has_active_si(sales_order):
        si = erpnext_delivery_note.make_sales_invoice(self.get('name'))
        si.insert()
        si = frappe.get_doc("Sales Invoice", si.name)
        si.save()
        try:
            si.submit()
        except Exception as ex:
            frappe.msgprint('Sales Invoice %s was created but not submitted due to the following error:\n%s' % (si.get('name'), cstr(ex)))
        else:
            frappe.msgprint('Sales Invoice %s was created and submitted automatically' % si.get('name'))
        frappe.clear_cache()
    else:
        for si in frappe.get_all('Sales Invoice', fields=['name'], filters={'sales_order': sales_order, 'docstatus': 0}):
            si = frappe.get_doc('Sales Invoice', si.get('name'))
            si.submit()
            frappe.msgprint('Sales Invoice %s was submitted automatically' % si.get('name'))
