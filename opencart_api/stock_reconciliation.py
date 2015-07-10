import frappe
from frappe import _
from erpnext.stock.utils import get_stock_balance
from frappe.utils.csvutils import read_csv_content_from_attached_file


@frappe.whitelist()
def clear_file_data(site_name):
    all_file_data = frappe.get_all('File Data', filters={'attached_to_doctype': 'Stock Reconciliation'})
    for file_data in all_file_data:
        frappe.get_doc('File Data', file_data.get('name')).delete()


@frappe.whitelist()
def get_items(warehouse, posting_date, posting_time):
    items = frappe.get_list("Item", fields=["name", "item_name"], filters={
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


@frappe.whitelist()
def get_items_from_file(doc_name, warehouse, posting_date, posting_time):
    res_items = []
    try:
        rows = read_csv_content_from_attached_file(frappe.get_doc("Stock Reconciliation", doc_name))
    except:
        frappe.throw(_("Please select a valid csv file with data"))

    # detect item_code, quantity, description
    is_header_detected = False
    item_code_idx = 0
    quantity_idx = 0
    description_idx = 0
    for row in rows:
        if not is_header_detected:
            try:
                robust_row = ['' if field is None else field.lower().strip() for field in row]
                item_code_idx = map(lambda a: a.startswith('item no') or a.startswith('item code'), robust_row).index(True)
                quantity_idx = map(lambda a: a.startswith('quantity'), robust_row).index(True)
                description_idx = map(lambda a: a.startswith('description'), robust_row).index(True)
            except ValueError:
                continue
            else:
                is_header_detected = True
                continue

        item_code = row[item_code_idx]
        quantity = row[quantity_idx]
        if isinstance(quantity, basestring):
            quantity = quantity.strip().replace(',', '')
            quantity = float(quantity) if quantity else None
        description = row[description_idx]
        if item_code is None or quantity is None or description is None:
            continue

        item_code = item_code.upper().strip()
        list_item = frappe.get_list('Item', fields=['name', 'item_name'], filters={'is_stock_item': 'Yes', 'name': item_code})
        if not list_item:
            continue
        item = list_item[0]
        item.item_code = item.name
        item.oc_item_name = item.item_name
        item.warehouse = warehouse
        item.qty = quantity
        # item.valuation_rate =
        item.current_qty = quantity
        # item.current_valuation_rate = item.valuation_rate
        del item["name"]
        res_items.append(item)

    return res_items
