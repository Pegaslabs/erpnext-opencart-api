from __future__ import unicode_literals
import frappe


from erpnext.stock.get_item_details import get_available_qty


def get_pos_profiles_item_details(company, args, pos_profiles=None):
    frappe.msgprint('get_pos_profiles_item_details...')
    res = frappe._dict()

    if not pos_profiles:
        pos_profiles = get_pos_profiles(company)

    if pos_profiles:
        for fieldname in ("income_account", "cost_center", "warehouse", "expense_account"):
            if not args.get(fieldname) and pos_profiles.get(fieldname):
                res[fieldname] = pos_profiles.get(fieldname)

        if res.get("warehouse"):
            res.actual_qty = get_available_qty(args.item_code, res.warehouse).get("actual_qty")

    return res


def get_pos_profiles(company):
    pos_profiles = frappe.db.sql("""select * from `tabPOS Profile` where user = %s
        and company = %s""", (frappe.session['user'], company), as_dict=1)

    if not pos_profiles:
        pos_profiles = frappe.db.sql("""select * from `tabPOS Profile`
            where ifnull(user,'') = '' and company = %s""", company, as_dict=1)

    return pos_profiles and pos_profiles[0] or None
