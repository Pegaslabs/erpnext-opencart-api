from __future__ import unicode_literals
from frappe.utils import now_datetime
import json

import frappe
import datetime
import oc_api


OPENCART_INIT_CACHE = {}

OPENCART_MANUFACTURERS_CACHE = {}

OPENCART_CATEGORIES_CACHE = {}

OC_CATEGORIES_CACHE_LAST_MODIFIED = None


def get_oc_init(site_name):
    global OPENCART_INIT_CACHE
    init_data = OPENCART_INIT_CACHE.get(site_name)
    if not init_data:
        success, data = oc_api.get(site_name).get_init()
        if not success:
            frappe.throw('Exception: Cannot get init data from Opencart site "%s"' % site_name)
        OPENCART_INIT_CACHE[site_name] = data
        init_data = data
    return init_data


def get(site_name):
    db_site = frappe.db.get('Opencart Site', {'name': site_name})
    if db_site:
        return frappe.get_doc('Opencart Site', db_site.get('name'))


def oc_validate(doc, method=None):
    site_name = doc.get('site_name')
    if not get(site_name):
        return

    # order status
    success, order_statuses = oc_api.get(site_name, use_pure_rest_api=True).get_order_statuses()
    if success:
        doc.update({
            'order_statuses_json': json.dumps(order_statuses)
        })

        # updating custom fields
        sales_order_oc_status = frappe.get_doc('Custom Field', 'Sales Order-oc_status')
        sales_order_oc_status.update({'options': '\n'.join(get_order_status_name_list(site_name))})
        sales_order_oc_status.save()

    # shipping methods
    success, shipping_methods = oc_api.get(site_name).get_shipping_methods()
    if success:
        doc.update({
            'shipping_methods_json': json.dumps(shipping_methods)
        })

    # payment methods
    success, payment_methods = oc_api.get(site_name).get_payment_methods()
    if success:
        doc.update({
            'payment_methods_json': json.dumps(payment_methods)
        })


@frappe.whitelist()
def test_connection(site_name):
    results = {}
    success, error = oc_api.get(site_name, use_pure_rest_api=True).check_connection()
    results['rest_api'] = {'success': success, 'error': error}
    success, error = oc_api.get(site_name, use_pure_rest_api=False).check_connection()
    results['rest_admin_api'] = {'success': success, 'error': error}
    return results


@frappe.whitelist()
def clear_file_data(site_name):
    all_file_data = frappe.get_all('File', filters={'attached_to_doctype': 'Opencart Site',
                                                    'attached_to_name': site_name})
    for file_data in all_file_data:
        frappe.get_doc('File', file_data.get('name')).delete()


def get_order_status_id(site, order_status_name):
    site_doc = site
    if isinstance(site, basestring):
        site_doc = frappe.get_doc('Opencart Site', site)
    order_statuses = json.loads(site_doc.get('order_statuses_json') or '[]')
    for order_status in order_statuses:
        if order_status.get('name') == order_status_name:
            return order_status.get('order_status_id')


@frappe.whitelist()
def get_order_status_name_list(site_name):
    status_name_list = []
    doc_site = get(site_name)
    if doc_site:
        status_name_list = [os.get('name') for os in json.loads(doc_site.get('order_statuses_json') or '[]')]
    return status_name_list


@frappe.whitelist()
def get_payment_method_code_list(site_name):
    code_list = []
    doc_site = get(site_name)
    if doc_site:
        code_list = [os.get('code') for os in json.loads(doc_site.get('payment_methods_json') or '[]')]
    return code_list


@frappe.whitelist()
def get_shipping_method_code_list(site_name):
    code_list = []
    doc_site = get(site_name)
    if doc_site:
        code_list = [os.get('code') for os in json.loads(doc_site.get('shipping_methods_json') or '[]')]
    return code_list

# @frappe.whitelist()
# def get_charts_for_country(country):
#     charts = []

#     def _get_chart_name(content):
#         if content:
#             content = json.loads(content)
#             if content and content.get("is_active", "No") == "Yes" and content.get("disabled", "No") == "No":
#                 charts.append(content["name"])

#     country_code = frappe.db.get_value("Country", country, "code")
#     if country_code:
#         path = os.path.join(os.path.dirname(__file__), "verified")
#         for fname in os.listdir(path):
#             if fname.startswith(country_code) and fname.endswith(".json"):
#                 with open(os.path.join(path, fname), "r") as f:
#                     _get_chart_name(f.read())

#     countries_use_OHADA_system = ["Benin", "Burkina Faso", "Cameroon", "Central African Republic", "Comoros",
#         "Congo", "Ivory Coast", "Gabon", "Guinea", "Guinea Bissau", "Equatorial Guinea", "Mali", "Niger",
#         "Replica of Democratic Congo", "Senegal", "Chad", "Togo"]

#     if country in countries_use_OHADA_system:
#         with open(os.path.join(os.path.dirname(__file__), "syscohada_syscohada_chart_template.json"), "r") as f:
#             _get_chart_name(f.read())

#     if len(charts) != 1:
#         charts.append("Standard")

#     return charts


def get_stock_status_id_by_name(site_name, stock_status_name):
    stock_statuses = get_oc_init(site_name).get('stock_statuses', [])
    res = next((ss.get('stock_status_id') for ss in stock_statuses if ss.get('name') == stock_status_name), None)
    if res is None:
        frappe.throw('Error. Cannot get stock status id by name "%s"' % stock_status_name)
    return res


def get_stock_status_name_by_id(site_name, stock_status_id):
    stock_statuses = get_oc_init(site_name).get('stock_statuses', [])
    return next((ss.get('name') for ss in stock_statuses if ss.get('stock_status_id') == stock_status_id), None)


def get_order_status_id_by_name(site_name, order_status_name):
    order_statuses = get_oc_init(site_name).get('order_statuses', [])
    return next((ss.get('stock_status_id') for ss in order_statuses if ss.get('name') == order_status_name), None)


def get_tax_rates(site_name):
    return get_oc_init(site_name).get('tax_rates', [])


def get_tax_rate_names(site_name):
    return [tax_rate.get('name') for tax_rate in get_tax_rates(site_name)]


def get_manufacturers(site_name):
    global OPENCART_MANUFACTURERS_CACHE
    manufacturers = OPENCART_MANUFACTURERS_CACHE.get(site_name)
    if manufacturers is None:
        manufacturers = list(oc_api.get(site_name).get_all_manufacturers())
        OPENCART_MANUFACTURERS_CACHE[site_name] = manufacturers
    return manufacturers


def get_manufacturer(site_name, manufacturer_id):
    manufacturers = get_manufacturers(site_name)
    for m in manufacturers:
        if m.get('manufacturer_id') == manufacturer_id:
            return m
    else:
        frappe.throw('Error. Cannot get manufacturer by manufacturer id "%s" for Opencart Site "%s"' % (manufacturer_id, site_name))


def get_manufacturer_name(site_name, manufacturer_id):
    manufacturers = get_manufacturers(site_name)
    return next((m.get('name') for m in manufacturers if m.get('manufacturer_id') == manufacturer_id), None)


def get_all_categories():
    global OPENCART_CATEGORIES_CACHE, OC_CATEGORIES_CACHE_LAST_MODIFIED
    modified_date = OC_CATEGORIES_CACHE_LAST_MODIFIED or now_datetime()
    now_date = now_datetime()
    categories = OPENCART_CATEGORIES_CACHE
    if not categories or now_date >= modified_date + datetime.timedelta(minutes=5):
        for site_name in frappe.db.get_all("Opencart Site", fields=["name"]):
            oc_site_categories = [frappe._dict(category) for category in list(oc_api.get(site_name).get_all_categories()) if category]
            OPENCART_CATEGORIES_CACHE[site_name.name] = oc_site_categories
            OC_CATEGORIES_CACHE_LAST_MODIFIED = now_datetime()
        categories = OPENCART_CATEGORIES_CACHE
    return categories


@frappe.whitelist()
def get_category_names():
    categories = get_all_categories()
    category_names = {}
    for i in categories:
        category_names[i] = [category.get("name") for category in categories[i]]
    return category_names

CAT = {}


def get_categories(site_name):
    global CAT
    if not CAT.get(site_name):
        categories = list(oc_api.get(site_name).get_all_categories())
        CAT[site_name] = categories
    return CAT.get(site_name)


def get_category_name(site_name, category_id):
    categories = get_categories(site_name)
    return next((m.get('name') for m in categories if m.get('category_id') == category_id), None)
