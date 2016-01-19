from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def get_sales_statistic(sales_order):
    back_order_no = frappe.db.get_values('Back Order', {'docstatus': '0', 'customer': frappe.db.get_value('Sales Order', sales_order, 'customer')}, 'name')
    delivery_note_no = frappe.db.get_values('Delivery Note', {'sales_order': sales_order}, 'name')
    sales_invoice_no = frappe.db.get_values('Sales Invoice', {'sales_order': sales_order}, 'name')
    packing_slip_no = frappe.db.get_values('Packing Slip', {'sales_order': sales_order}, 'name')
    return {
        'back_order': back_order_no,
        'delivery_note': delivery_note_no,
        'sales_invoice': sales_invoice_no,
        'packing_slip': packing_slip_no
    }


@frappe.whitelist()
def get_inventory_exchange_entry(sales_invoice):
    return frappe.db.get_values('Inventory Exchange Entry', {'sales_invoice': sales_invoice}, 'name')
