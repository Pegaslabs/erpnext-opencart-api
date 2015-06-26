from __future__ import unicode_literals
import json

import frappe

import oc_api


def get(site_name):
    db_site = frappe.db.get('Opencart Site', {'name': site_name})
    if db_site:
        return frappe.get_doc('Opencart Site', db_site.get('name'))


def oc_validate(doc, method=None):
    site_name = doc.get('site_name')

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
