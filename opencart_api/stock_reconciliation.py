import frappe
from erpnext.stock.utils import get_stock_balance


@frappe.whitelist()
def get_items(warehouse, posting_date, posting_time):
    items = frappe.get_list("Item", fields=["name", "item_name", "oc_model"], filters={
        "is_stock_item": "Yes",
        "has_serial_no": "No",
        "has_batch_no": "No"
    })
    for item in items:
        item.item_code = item.name
        item.oc_item_name = item.item_name
        item.warehouse = warehouse
        item.qty, item.valuation_rate = get_stock_balance(item.name, warehouse, posting_date, posting_time, with_valuation_rate=True)
        item.current_qty = item.qty
        item.current_valuation_rate = item.valuation_rate
        del item["name"]

    return items
