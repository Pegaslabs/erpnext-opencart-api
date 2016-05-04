from __future__ import unicode_literals
import posixpath
import frappe
from models import (OpencartCategory,
                    OpencartProductOption,
                    OpencartProductOptionExt,
                    OpencartStore,
                    OpencartCustomerGroup,
                    OpencartOrder)
from utils import oc_request, oc_upload_file


def get(site_name, api_base_url=None, use_pure_rest_api=False):
        '''This method assumes to use Opencart REST Admin API'''
        site_doc = frappe.get_doc("Opencart Site", site_name)
        if use_pure_rest_api:
            headers = {site_doc.get('opencart_header_key'): site_doc.get('opencart_header_value')}
        else:
            headers = {site_doc.get('opencart_admin_header_key'): site_doc.get('opencart_admin_header_value')}
        opencart_api = OpencartApi(api_base_url if api_base_url else site_doc.get('server_base_url'),
                                   use_pure_rest_api=use_pure_rest_api,
                                   headers=headers)
        return opencart_api


class OpencartApi(object):

    def __init__(self, base_api_url, use_pure_rest_api=False, headers={}):
        self._url = posixpath.join(base_api_url, 'api', 'rest')
        self.use_pure_rest_api = use_pure_rest_api
        self._headers = headers
        # self._headers.update({'Accept': 'application/json'})
        # text/plain; charset=UTF-8
        # self._headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:11.0) Gecko/20100101 Firefox/11.0'})

    def __str__(self):
        return "OpencartApi at %s" % (self._url,)

    @property
    def url(self):
        return self._url

    @property
    def headers(self):
        return self._headers

    def get_categories_by_level(self, level=1):
        success, resp = oc_request(self.url + '/categories/level/%s' % str(level), headers=self.headers)
        if not success:
            return
        categories_resp = resp.get('data').get('categories', {})
        for c in categories_resp:
            yield OpencartCategory(self, categories_resp.get(c)[0], level=level)

    def get_categories_by_parent(self, parent_id):
        success, resp = oc_request(self.url + '/categories/parent/%s' % parent_id, headers=self.headers)
        if not success:
            return
        categories_resp = resp.get('data').get('categories', {})
        for c in categories_resp:
            yield OpencartCategory(self, categories_resp.get(c)[0], parent=parent_id)

    def get_all_categories(self):
        success, resp = oc_request(self.url + '/list_all_categories', headers=self.headers, method='GET')
        return resp.get('data', []) if success else []

    def get_all_products(self, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/products/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            if not success or not resp.get('data'):
                break
            page += 1
            for c in resp.get('data', {}):
                yield c

    def get_product_options(self, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/product_options/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            if not success or not resp.get('data'):
                break
            page += 1
            for po in resp.get('data'):
                yield OpencartProductOption(self, po)

    def get_products_by_category(self, category_id, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/products/category/%s/limit/%s/page/%s' % (category_id, str(limit), str(page)), headers=self.headers)
            if not success or not resp.get('data'):
                break
            page += 1
            for c in resp.get('data', {}):
                c['category_id'] = category_id
                c['product_id'] = c.get('product_id') or c.get('id')
                for i, first_description in c.get('product_description').items():
                    if isinstance(first_description, list):
                        for k, val in first_description[0].items():
                            c[k] = val
                        break
                    else:
                        for k, val in first_description.items():
                            c[k] = val
                    if i.isdigit():
                        break
                    else:
                        c[i] = first_description
                c['options_list'] = [OpencartProductOptionExt(self, o) for o in c.get('options')] if c.get('options') else []
                yield c

    def fix_product_resp(self, product):
        product['product_id'] = product.get('product_id') or product.get('id')

        # resolving category_id
        if isinstance(product.get('category'), dict):
            for category_id, first_category in product.get('category').items():
                product['category_id'] = category_id
                break

        for i, first_description in product.get('product_description', {}).items():
            if isinstance(first_description, list):
                for k, val in first_description[0].items():
                    product[k] = val
                break
            else:
                for k, val in first_description.items():
                    product[k] = val
            if i.isdigit():
                break
            else:
                product[i] = first_description

    def get_product(self, product_id):
        success, resp = oc_request(self.url + '/products/%s' % product_id, headers=self.headers)
        product = resp.get('data', {})
        self.fix_product_resp(product)
        return (success, product)

    def get_product_by_sku(self, sku):
        success, resp = oc_request(self.url + '/products_by_sku/%s' % sku, headers=self.headers)
        product = resp.get('data', {})
        self.fix_product_resp(product)
        return (success, product)

    def get_product_by_model(self, model):
        success, resp = oc_request(self.url + '/products_by_model/%s' % model, headers=self.headers)
        product = resp.get('data', {})
        self.fix_product_resp(product)
        return (success, product)

    def create_product(self, data):
        success, resp = oc_request(self.url + '/products', headers=self.headers, method='POST', data=data)
        return (success, str(resp.get('product_id', '')))

    def update_product(self, product_id, data):
        success, resp = oc_request(self.url + '/products/%s' % product_id, headers=self.headers, method='PUT', data=data)
        return success

    def delete_product(self, product_id):
        success, resp = oc_request(self.url + '/products/%s' % product_id, headers=self.headers, method='DELETE')
        return success

    def set_product_image(self, product_id, file_path):
        success, resp = oc_upload_file(self.url + '/products/%s/images' % product_id, file_path, headers=self.headers)
        return success

    def get_stores(self):
        success, resp = oc_request(self.url + '/stores', headers=self.headers)
        if not success:
            return
        stores = resp.get('data')
        if isinstance(stores, dict):
            yield OpencartStore(self, stores)
            for i in stores:
                if i.isdigit():
                    yield OpencartStore(self, stores.get(i))
        elif isinstance(stores, list):
            for i in stores:
                yield OpencartStore(self, i)
        else:
            return

    def get_customer_groups(self, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/customergroups/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            customer_groups = resp.get('data')
            if not success or not customer_groups:
                break
            page += 1
            for g in customer_groups:
                yield OpencartCustomerGroup(self, customer_groups.get(g)[0])

    def get_customer_group_json(self, limit=100, page=1, language_id=1):
        # for now just ignoring language_id
        while True:
            success, resp = oc_request(self.url + '/customergroups/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            customer_groups = resp.get('data', {})
            if not success or not customer_groups:
                break
            page += 1
            for g in customer_groups:
                yield customer_groups.get(g)[0]

    def get_customer_group(self, customer_group_id):
        for customer_group in self.get_customer_group_json():
            if customer_group.get('customer_group_id') == customer_group_id:
                return (True, customer_group)
        return (False, {})

    def get_customer(self, customer_id):
        success, resp = oc_request(self.url + '/customers/%s' % customer_id, headers=self.headers)
        return (success, resp.get('data', {}))

    def create_customer(self, data):
        success, resp = oc_request(self.url + '/customers', headers=self.headers, method='POST', data=data)
        return (success, resp)

    def update_customer(self, customer_id, data):
        success, resp = oc_request(self.url + '/customers/%s' % customer_id, headers=self.headers, method='PUT', data=data)
        return (success, resp)

    def delete_customer(self, customer_id):
        data = {'customers': [customer_id]}
        success, resp = oc_request(self.url + '/customers', headers=self.headers, method='DELETE', data=data)
        return (success, resp)

    def get_customers(self, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/customers/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            if not success or not resp.get('data'):
                break
            page += 1
            for c in resp.get('data'):
                yield self.get_customer(c.get('customer_id'))

    def get_order(self, order_id):
        success, resp = oc_request(self.url + '/orders/%s' % order_id, headers=self.headers)
        order = resp.get('data')
        return OpencartOrder(self, order) if order else None

    def get_order_json(self, order_id):
        success, resp = oc_request(self.url + '/orders/%s' % order_id, headers=self.headers)
        return (success, resp.get('data', {}))

    def create_order(self, data):
        success, resp = oc_request(self.url + '/orderadmin', headers=self.headers, method='POST', data=data)
        return (success, resp)

    def update_order(self, order_id, data):
        success, resp = oc_request(self.url + '/orders/%s' % order_id, headers=self.headers, method='PUT', data=data)
        return (success, resp)

    def delete_order(self, order_id):
        data = {'orders': [order_id]}
        success, resp = oc_request(self.url + '/orders/%s' % order_id, headers=self.headers, method='DELETE', data=data)
        return (success, resp)

    def get_orders_by_customer(self, customer_id):
        success, resp = oc_request(self.url + '/orders/user/%s' % customer_id, headers=self.headers)
        if not success:
            return
        for o in resp.get('data'):
            yield self.get_order(o.get('order_id'))

    def get_orders_modified_from_to(self, modified_from, modified_to):
        success, resp = oc_request(self.url + '/orders/details/modified_from/%s/modified_to/%s' % (modified_from, modified_to), headers=self.headers)
        return (success, resp.get('data', []) if success else [])

    def get_orders_addeed_from_to(self, added_from, added_to):
        success, resp = oc_request(self.url + '/orders/details/added_from/%s/added_to/%s' % (added_from, added_to), headers=self.headers)
        return (success, resp.get('data', []) if success else [])

    def get_orders(self):
        success, resp = oc_request(self.url + '/orders', headers=self.headers)
        if not success:
            return
        for o in resp.get('data'):
            yield self.get_order(o.get('order_id'))

    def check_connection(self):
        if self.use_pure_rest_api:
            success, resp = oc_request(self.url + '/languages', headers=self.headers)
        else:
            success, resp = oc_request(self.url + '/countries', headers=self.headers)
        return (success, resp.get('error', ''))

    def get_init(self):
        success, resp = oc_request(self.url + '/init', headers=self.headers)
        return (success, resp.get('data', {}) if success else {})

    def get_order_statuses(self):
        success, resp = oc_request(self.url + '/order_statuses', headers=self.headers)
        return (success, resp.get('data', []) if success else [])

    def get_shipping_methods(self):
        success, resp = oc_request(self.url + '/shippingmethods', headers=self.headers)
        return (success, resp.get('data', []) if success else [])

    def get_payment_methods(self):
        success, resp = oc_request(self.url + '/paymentmethods', headers=self.headers)
        return (success, resp.get('data', []) if success else [])

    def get_all_manufacturers(self, limit=100, page=1):
        while True:
            success, resp = oc_request(self.url + '/manufacturers/limit/%s/page/%s' % (str(limit), str(page)), headers=self.headers)
            if not success or not resp.get('data'):
                break
            page += 1
            for c in resp.get('data', []):
                yield c

    def get_warehouses(self):
        success, resp = oc_request(self.url + '/warehouses', headers=self.headers)
        return (success, resp.get('data', []) if success else [])
