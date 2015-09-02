from __future__ import unicode_literals

import frappe
from frappe.utils import flt, cstr
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.delivery_note import delivery_note as erpnext_delivery_note
from erpnext.selling.doctype.sales_order import sales_order as erpnext_sales_order


def validate(doc, method=None):
    pass


def before_submit(self, method=None):
    # nothing to do for if it's return
    if self.is_return:
        return

    packing_slips = frappe.db.get_values('Packing Slip', {'delivery_note': self.name, 'docstatus': 1}, 'name', as_dict=True)
    if len(packing_slips) > 1:
        frappe.throw('Cannot submit: this Delivery Note has more than one Packing Slips')
    elif len(packing_slips) == 0:
        frappe.throw('Please submit at first the Packing Slip')
    if not self.oc_tracking_number:
        frappe.throw('Please submit at first the Packing Slip.\nTracking number is missed in this Delivery Note document.')
    ps = frappe.get_doc('Packing Slip', packing_slips[0].get('name'))
    dn_details, ps_item_qty, no_of_cases = ps.get_details_for_packing()
    dn_details_map = {dn_detail.get('item_code'): dn_detail for dn_detail in dn_details}

    if self.back_order_items:
        back_orders = frappe.db.get_all('Back Order', filters={'sales_order': self.sales_order, 'docstatus': 0})
        if self.sales_order and len(back_orders) > 1:
            frappe.throw('Only one Back Order can be linked with Sales Order')
        elif self.sales_order and len(back_orders) == 1:
            doc_back_order = frappe.get_doc('Back Order', back_orders[0].get('name'))
            new_doc_back_order = make_back_order(self.name, packing_slip_doc=ps)
            back_order_item_map = {i.item_code: i for i in doc_back_order.items}
            for new_bo_item in new_doc_back_order.items:
                bo_item = back_order_item_map.get(new_bo_item.get('item_code'))
                if bo_item:
                    bo_item.update({
                        'qty': flt(bo_item.qty) + flt(new_bo_item.qty),
                        'amount': (flt(bo_item.qty) + flt(new_bo_item.qty)) * flt(bo_item.rate)})
                    bo_item.save()
                else:
                    doc_back_order.append('items', {
                        'item_code': new_bo_item.item_code,
                        'item_name': new_bo_item.item_name,
                        'description': new_bo_item.description,
                        'stock_uom': new_bo_item.stock_uom,
                        'qty': flt(new_bo_item.qty),
                        'amount': flt(new_bo_item.amount),
                        'rate': new_bo_item.rate,
                        'warehouse': new_bo_item.warehouse,
                        'discount_percentage': new_bo_item.discount_percentage,
                        'price_list_rate': new_bo_item.price_list_rate,
                        'base_price_list_rate': new_bo_item.base_price_list_rate,
                        'base_amount': new_bo_item.base_amount,
                        'base_rate': new_bo_item.base_rate,
                        'prevdoc_docname': new_bo_item.prevdoc_docname,
                        'image': new_bo_item.image
                    })
            doc_back_order.save()
            frappe.msgprint('Back Order %s is updated successfully' % (back_orders[0].get('name'),))
            update_delivery_note_from_packing_slip(self, ps)
            frappe.clear_cache()
        else:
            doc_back_order = make_back_order(self.name, packing_slip_doc=ps)
            doc_back_order.save()
            frappe.msgprint('Back Order %s is created and linked to Sales Order %s' % (doc_back_order.name, self.sales_order))
            update_delivery_note_from_packing_slip(self, ps)
            frappe.clear_cache()
    else:
        if len(self.items) > len(dn_details):
            frappe.msgprint('Please enable back order items or adjust items manually.')
            frappe.throw('Some items from Delivery Note were not packed in Packing Slip %s.' % ps.name)
        for item in dn_details:
            if flt(item.get('packed_qty')) < flt(item.get('qty')):
                frappe.msgprint('Please enable back order items or adjust items manually.')
                frappe.throw('Only %s of %s %s items from Delivery Note were packed in Packing Slip %s.' % (cstr(item.get('packed_qty')), cstr(item.get('qty')), item.get('item_code'), ps.name))


def update_delivery_note_from_packing_slip(doc_delivery_note, packing_slip_doc):
    ps_item_map = {i.item_code: i for i in packing_slip_doc.items}
    delivery_note_item_map = {i.item_code: i for i in doc_delivery_note.items}
    for dn_item_code, dn_doc_item in delivery_note_item_map.items():
        dln_doc_item = ps_item_map.get(dn_item_code)
        if dln_doc_item:
            dn_doc_item.update({
                'qty': flt(dln_doc_item.qty),
            })
        else:
            doc_delivery_note.items.remove(dn_doc_item)
        if len(doc_delivery_note.items) > 1 and dn_doc_item.qty == 0:
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
        si.submit()
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


@frappe.whitelist()
def make_packing_slip(source_name, target_doc=None):

    db_packing_slip_docstatus = frappe.db.get_value('Packing Slip', {'delivery_note': source_name}, 'docstatus')
    if db_packing_slip_docstatus is not None and db_packing_slip_docstatus != 2:
        frappe.throw('Cannot make new Packing Slip: Packing Slip is already created and its docstatus is not canceled.')

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Packing Slip",
            "field_map": {
                "name": "delivery_note",
                "letter_head": "letter_head"
            },
            "validation": {
                "docstatus": ["=", 0]
            }
        }
    }, target_doc)

    return doclist


def on_delivery_note_added(delivery_note):
    pass
