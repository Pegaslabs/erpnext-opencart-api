from __future__ import unicode_literals

import frappe
from frappe.utils import flt, cstr
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.delivery_note import delivery_note as erpnext_delivery_note
from erpnext.selling.doctype.sales_order import sales_order as erpnext_sales_order


def update_delivery_note_from_packing_slip(doc_delivery_note, packing_slip_doc):
    ps_item_map = {i.item_code: i for i in packing_slip_doc.items}
    dn_item_map = {i.item_code: i for i in doc_delivery_note.items}
    for dn_item_code, dn_doc_item in dn_item_map.items():
        dln_doc_item = ps_item_map.get(dn_item_code)
        if dln_doc_item:
            dn_doc_item.update({
                'qty': flt(dln_doc_item.qty),
            })
        else:
            doc_delivery_note.items.remove(dn_doc_item)
        if len(doc_delivery_note.items) > 1 and dn_doc_item.qty == 0 and dn_doc_item in doc_delivery_note.items:
            doc_delivery_note.items.remove(dn_doc_item)
        doc_delivery_note.validate()
    sales_order = frappe.db.get_value('Delivery Note', doc_delivery_note.name, 'sales_order')
    if erpnext_sales_order.has_active_si(sales_order):
        si = frappe.get_doc('Sales Invoice', {'sales_order': sales_order})
        si.delete()


def on_submit(self, method=None):
    sales_order = frappe.db.get_value('Delivery Note', self.name, 'sales_order')
    if not erpnext_sales_order.has_active_si(sales_order):
        si = erpnext_delivery_note.make_sales_invoice(self.get('name'))
        si.insert()
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


@frappe.whitelist()
def make_back_order(source_name, target_doc=None, packing_slip_doc=None):
    dn_details, ps_item_qty, no_of_cases = packing_slip_doc.get_details_for_packing()
    dn_details_map = {dn_detail.get('item_code'): dn_detail for dn_detail in dn_details}

    def postprocess(source, target):
        target.items = [item for item in target.items if item.qty > 0]

    def update_item(obj, target, source_parent):
        dn_item = dn_details_map.get(obj.item_code)
        if dn_item:
            target.qty = flt(dn_item.get('qty')) - flt(dn_item.get('packed_qty')) if flt(dn_item.get('qty')) > flt(dn_item.get('packed_qty')) else 0
            target.base_amount = flt(target.qty) * flt(obj.base_rate)
            target.amount = flt(target.qty) * flt(obj.rate)
        else:
            target.qty = flt(obj.qty)
            target.base_amount = flt(obj.qty) * flt(obj.base_rate)
            target.amount = flt(obj.qty) * flt(obj.rate)

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Back Order",
            "field_map": {
                "sales_order": "sales_order",
            },
            "validation": {
                "docstatus": ["=", 0]
            }
        },
        "Delivery Note Item": {
            "doctype": "Back Order Item",
            "field_map": {
                # "parent": "prevdoc_docname"
            },
            "postprocess": update_item
        }
    }, target_doc, postprocess)

    return doclist


def on_delivery_note_added(delivery_note):
    pass
