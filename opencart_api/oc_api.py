from __future__ import unicode_literals
import posixpath
import frappe
from models import (OpencartCategory,
                    OpencartProduct,
                    OpencartProductOption,
                    OpencartStore,
                    OpencartCustomerGroup,
                    OpencartCustomer,
                    OpencartOrder)
from utils import oc_get_request


def get(site_name):
        site_doc = frappe.get_doc("Opencart Site", site_name)
        headers = {site_doc.get('opencart_admin_header_key'): site_doc.get('opencart_admin_header_value')}
        opencart_api = OpencartApi(site_doc.get('server_base_url'), headers)
        return opencart_api


class OpencartApi(object):

    def __init__(self, base_api_url, headers={}):
        self._url = posixpath.join(base_api_url, 'api', 'rest')
        self._headers = headers

    def __str__(self):
        return "OpencartApi at %s" % (self._url,)

    @property
    def url(self):
        return self._url

    @property
    def headers(self):
        return self._headers

    def get_categories_by_level(self, level=1):
        success, resp = oc_get_request(self.url + '/categories/level/%s' % str(level), self.headers)
        if not success:
            return
        categories_resp = resp.get('categories', {})
        for c in categories_resp:
            yield OpencartCategory(self, categories_resp.get(c)[0], level=level)

    def get_categories_by_parent(self, parent_id):
        success, resp = oc_get_request(self.url + '/categories/parent/%s' % parent_id, self.headers)
        if not success:
            return
        categories_resp = resp.get('categories', {})
        for c in categories_resp:
            yield OpencartCategory(self, categories_resp.get(c)[0], parent=parent_id)

    def get_all_categories(self, parent_id=None):
        if parent_id:
            categories = self.get_categories_by_parent(parent_id)
        else:
            categories = self.get_categories_by_level()
        for category in categories:
            yield category
            for sub_category in self.get_all_categories(category.category_id):
                yield sub_category

    def get_all_products(self, limit=100, page=1):
        while True:
            success, resp = oc_get_request(self.url + '/products/limit/%s/page/%s' % (str(limit), str(page)), self.headers)
            if not success or not resp:
                break
            page += 1
            for c in resp:
                yield OpencartProduct(self, c)

    def get_product_options(self, limit=100, page=1):
        while True:
            success, resp = oc_get_request(self.url + '/product_options/limit/%s/page/%s' % (str(limit), str(page)), self.headers)
            if not success or not resp:
                break
            page += 1
            for po in resp:
                yield OpencartProductOption(self, po)

    def get_products_by_category(self, category_id, limit=100, page=1):
        while True:
            success, resp = oc_get_request(self.url + '/products/category/%s/limit/%s/page/%s' % (category_id, str(limit), str(page)), self.headers)
            if not success or not resp:
                break
            page += 1
            for c in resp:
                yield OpencartProduct(self, c)

    def get_stores(self):
        success, resp = oc_get_request(self.url + '/stores', self.headers)
        if not success:
            return
        yield OpencartStore(self, resp)
        for i in resp:
            if i.isdigit():
                yield OpencartStore(self, resp.get(i))

    def get_customer_groups(self, limit=100, page=1):
        while True:
            success, resp = oc_get_request(self.url + '/customergroups/limit/%s/page/%s' % (str(limit), str(page)), self.headers)
            if not success or not resp:
                break
            page += 1
            for g in resp:
                yield OpencartCustomerGroup(self, resp.get(g)[0])

    def get_customer(self, customer_id):
        success, resp = oc_get_request(self.url + '/customers/%s' % customer_id, self.headers)
        return OpencartCustomer(self, resp) if resp else None

    def get_customers(self, limit=100, page=1):
        while True:
            success, resp = oc_get_request(self.url + '/customers/limit/%s/page/%s' % (str(limit), str(page)), self.headers)
            if not success or not resp:
                break
            page += 1
            for c in resp:
                yield self.get_customer(c.get('customer_id'))

    def get_order(self, order_id):
        success, resp = oc_get_request(self.url + '/orders/%s' % order_id, self.headers)
        return OpencartOrder(self, resp) if resp else None

    def get_order_details(self, order_id):
        success, resp = oc_get_request(self.url + '/orders/%s' % order_id, self.headers)
        return OpencartOrder(self, resp) if resp else None

    def get_orders_by_customer(self, customer_id):
        success, resp = oc_get_request(self.url + '/orders/user/%s' % customer_id, self.headers)
        if not success:
            return
        for o in resp:
            yield self.get_order(o.get('order_id'))

    def get_orders(self):
        success, resp = oc_get_request(self.url + '/orders', self.headers)
        if not success:
            return
        for o in resp:
            yield self.get_order(o.get('order_id'))
