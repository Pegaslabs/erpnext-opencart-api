from __future__ import unicode_literals

import frappe


def get_bin_location(item_code, warehouse):
    return frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "bin_location")


@frappe.whitelist()
def get_inventory_per_warehouse(item_code):
    return frappe.db.get_values("Bin", {"item_code": item_code}, ["warehouse", "actual_qty", "stock_value"])
