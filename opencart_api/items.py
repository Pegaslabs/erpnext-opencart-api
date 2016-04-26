from datetime import datetime

import frappe
from frappe import _
from frappe.utils import get_files_path
from frappe.utils import cstr, flt, getdate
from frappe.utils.dateutils import parse_date
from frappe.utils.csvutils import read_csv_content_from_attached_file

import oc_api
import oc_site
import brands
import customer_groups
import item_groups
from decorators import sync_item_to_opencart
from utils import sync_info


CURRENCY_TO_PRICE_FIELD_MAP = {
    'GBP': 'price_gbp',
    'EUR': 'price_eur',
    'USD': 'price_usd',
    'CAD': 'price_cad'
}


def get_price_field_name(currency):
    return CURRENCY_TO_PRICE_FIELD_MAP.get(currency, 'price')


def get_oc_product_price(oc_product, currency):
    if oc_product.get('prices'):
        for product_price in oc_product.get('prices'):
            if product_price.get('code') == currency:
                return flt(product_price.get('price'))
        else:
            frappe.throw('Could not get price from discount for currency %s' % currency)
    else:
        return flt(oc_product.get('price'))


def update_oc_product_price(doc_oc_product, price, currency):
    if doc_oc_product.multi_currency_price:
        doc_oc_product.update({get_price_field_name(currency): price})
    else:
        doc_oc_product.update({'price': price})


def get_oc_discount_price(oc_discount, currency):
    if oc_discount.get('prices'):
        for discount_price in oc_discount.get('prices'):
            if discount_price.get('code') == currency:
                return float(discount_price.get('price', 0))
        else:
            frappe.throw('Could not get price from discount for currency %s' % currency)
    else:
        return float(oc_discount.get('price', 0))


def check_readiness_to_sync_product_to_oc(doc_oc_product, oc_product):
    check_map = (
        ('oc_model', 'model'),
        ('oc_sku', 'sku'),
        ('oc_tax_class_id', 'tax_class_id'),
        ('oc_manufacturer_id', 'manufacturer_id'),
        ('oc_status', 'status')
    )
    for check_item in check_map:
        if cstr(doc_oc_product.get(check_item[0])) != cstr(oc_product.get(check_item[1])):
            frappe.throw("Value of \"{}\" field is out of sync with the field of Opencart product on {} site".format(doc_oc_product.meta.get_label(check_item[0]), doc_oc_product))

    if cstr(doc_oc_product.get('oc_stock_status_id')) != oc_site.get_stock_status_id_by_name(doc_oc_product.oc_site, oc_product.get('stock_status')):
        frappe.throw("Value of \"{}\" field is out of sync with the field of Opencart product on {} site".format(doc_oc_product.meta.get_label('oc_stock_status_id'), doc_oc_product))

    if bool(doc_oc_product.multi_currency_price) != bool(oc_product.get('prices')):
        frappe.throw("Multi currency price inconsistence for Item {}".format(doc_oc_product.oc_model))

    # check multi currency prices
    if oc_product.get('prices'):
        for product_price in oc_product.get('prices'):
            if product_price.get('code') and get_price_field_name(product_price.get('code')):
                price_field_name = get_price_field_name(product_price.get('code'))
                if cstr(flt(doc_oc_product.get(price_field_name))) != cstr(flt(product_price.get('price'))):
                    frappe.throw("Value of \"{}\" field is out of sync with the field of Opencart product on {} site".format(doc_oc_product.meta.get_label('price'), doc_oc_product))
                break
        else:
            frappe.throw('Could not get price from oc product for currency {}'.format(product_price.get('code')))
    else:
        if cstr(flt(doc_oc_product.price)) != cstr(flt(oc_product.get('price'))):
            frappe.throw("Value of \"{}\" field is out of sync with the field of Opencart product on {} site".format(doc_oc_product.meta.get_label('price'), doc_oc_product))

    # # specials
    # product_special = []
    # for doc_oc_special in doc_item.oc_specials:
    #     if cur_site_name != doc_oc_special.get('oc_site'):
    #         continue
    #     doc_customer_group = frappe.get_doc('Customer Group', doc_oc_special.get('customer_group'))
    #     customer_group_id = doc_customer_group.get('oc_customer_group_id')
    #     if not customer_group_id:
    #         continue
    #     if cur_site_name != doc_customer_group.get('oc_site'):
    #         frappe.throw('Customer Group "%s" does not exist in Opencart site "%s"' % (doc_customer_group.get('name'), cur_site_name))
    #     product_special.append({
    #         'customer_group_id': customer_group_id,
    #         'price': doc_oc_special.price,
    #         'priority': doc_oc_special.priority,
    #         'date_start': doc_oc_special.date_start.strftime("%Y-%m-%d") if doc_oc_special.date_start else '',
    #         'date_end': doc_oc_special.date_end.strftime("%Y-%m-%d") if doc_oc_special.date_end else '',
    #     })
    # data['product_special'] = product_special

    # # discounts
    # product_discount = []
    # for doc_oc_discount in doc_item.oc_discounts:
    #     if cur_site_name != doc_oc_discount.get('oc_site'):
    #         continue
    #     doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
    #     customer_group_id = doc_customer_group.get('oc_customer_group_id')
    #     if not customer_group_id:
    #         continue
    #     if cur_site_name != doc_customer_group.get('oc_site'):
    #         frappe.throw('Customer Group "%s" does not exist in Opencart site "%s"' % (doc_customer_group.get('name'), cur_site_name))
    #     product_discount_json = {
    #         'customer_group_id': customer_group_id,
    #         'price': doc_oc_discount.price,
    #         'priority': doc_oc_discount.priority,
    #         'quantity': doc_oc_discount.quantity,
    #         'date_start': doc_oc_discount.date_start.strftime("%Y-%m-%d") if doc_oc_discount.date_start else '',
    #         'date_end': doc_oc_discount.date_end.strftime("%Y-%m-%d") if doc_oc_discount.date_end else '',
    #     }
    #     # update multi currency prices for discount
    #     if doc_oc_discount.multi_currency_price:
    #         prices = []
    #         for currency_code, price_field_name in CURRENCY_TO_PRICE_FIELD_MAP.items():
    #             prices.append({
    #                 'price': str(doc_oc_discount.get(price_field_name)) if doc_oc_discount.get(price_field_name) is not None else '',
    #                 'code': currency_code,
    #             })
    #         product_discount_json.update({
    #             'prices': prices
    #         })
    #     product_discount.append(product_discount_json)


def sync_item_to_oc(item_code, doc_item=None, site_name=None):
    if not doc_item:
        doc_item = frappe.get_doc("Item", {"item_code": item_code})
    for doc_oc_product in doc_item.get('oc_products'):
        if not doc_oc_product.get('oc_sync_to'):
            continue
        cur_site_name = doc_oc_product.get('oc_site')
        if site_name and cur_site_name != site_name:
            continue
        oc_product_id = doc_oc_product.get('oc_product_id')
        get_product_success, oc_product = oc_api.get(cur_site_name).get_product(oc_product_id)
        # check_readiness_to_sync_product_to_oc(doc_oc_product, oc_product)
        data = {
            'model': doc_oc_product.get('oc_model') or doc_item.get('name'),  # mandatory
            'sku': doc_oc_product.get('oc_sku') or doc_oc_product.get('oc_model'),  # mandatory
            'quantity': doc_oc_product.get('oc_quantity') or '0',  # mandatory
            'price': doc_oc_product.get('price'),
            'tax_class_id': doc_oc_product.get('oc_tax_class_id'),  # mandatory
            'manufacturer_id': doc_oc_product.get('oc_manufacturer_id'),  # mandatory
            # 'sort_order': '1',  # mandatory
            'status': doc_oc_product.get('oc_status'),
            # ,
            # 'upc': '',
            # 'ean': '',
            # 'jan': '',
            # 'isbn': '',
            # 'mpn': '',
            # 'location': '',
            'stock_status_id': doc_oc_product.get('oc_stock_status_id')
            # 'reward': '400',
            # 'points': '200',
            # 'image': doc_oc_product.get('image'),
            # 'other_images': [
            #     'catalog/image/image2.png',
            #     'catalog/image/image3.png'
            # ],
            # 'date_available': '2009-02-03',
            # 'weight': '146.4',
            # 'weight_class_id': '2',
            # 'length': '10',
            # 'width': '20',
            # 'height': '2',
            # 'length_class_id': '1',
            # 'subtract': '1',
            # 'minimum': '1',
            # 'product_store': [  # mandatory
            #     '12'
            # ],
            # 'product_category': [
            #     doc_item_group.get('oc_category_id')
            # ],
            # 'product_description': [
            #     {
            #         'language_id': 1,
            #         'name': doc_item.get('item_name'),
            #         'description': doc_item.get('description'),
            #         'meta_description': doc_item.get('oc_meta_description'),
            #         'meta_title': doc_item.get('oc_meta_title'),
            #         'meta_keyword': doc_item.get('oc_meta_keyword'),
            #     }
            #     # ,
            #     # {
            #     # 'language_id': 2,
            #     # 'name': 'test product hun',
            #     # 'meta_title': 'test product meta_title',
            #     # 'meta_description': 'test product meta_description hu',
            #     # 'meta_keyword': 'test product meta_keyword hun',
            #     # 'description': 'test product description hu'
            #     # }
            # ]
            # 'product_option': [
            # {
            #     'product_option_value': [
            #     {
            #         'price': 10,
            #         'price_prefix': '+',
            #         'subtract': '0',
            #         'points': '0',
            #         'points_prefix': '0',
            #         'weight': '0',
            #         'weight_prefix': '0',
            #         'option_value_id': '46',
            #         'quantity': '300'
            #     },
            #     {
            #         'price': 20,
            #         'price_prefix': '+',
            #         'subtract': '0',
            #         'points': '0',
            #         'points_prefix': '0',
            #         'weight': '0',
            #         'weight_prefix': '0',
            #         'option_value_id': '47',
            #         'quantity': '500'
            #     },
            #     {
            #         'price': false,
            #         'price_prefix': '+',
            #         'subtract': '0',
            #         'points': '0',
            #         'points_prefix': '0',
            #         'weight': '0',
            #         'weight_prefix': '0',
            #         'option_value_id': '48',
            #         'quantity': '10'
            #     }
            #     ],
            #     'type': 'select',
            #     'required': '1',
            #     'option_id': '11'
            # },
            # {
            #     'option_value': 'demo text option value',
            #     'type': 'text',
            #     'required': '1',
            #     'option_id': '4'
            # }
            # ],
            # 'product_attribute': [
            #     {
            #         'attribute_id': '16',
            #         'product_attribute_description':
            #         [
            #             {
            #             'language_id': '1',
            #             'text': 'demo attribute value'
            #             }
            #         ]
            #     }
            # ]
            # ,'product_special':[
            #     {
            #         'customer_group_id':'1',
            #         'price':'10',
            #         'priority':'1',
            #         'date_start':'2015-02-23',
            #         'date_end':'2015-02-27'
            #     },
            #     {
            #         'customer_group_id':'1',
            #         'price':'8',
            #         'priority':'1',
            #         'date_start':'2015-02-23',
            #         'date_end':'2015-02-27'
            #     }
            # ]
            # ,'product_discount':[
            #     {
            #         'customer_group_id':'1',
            #         'price':'10',
            #         'priority':'1',
            #         'quantity':'10',
            #         'date_start':'2015-02-23',
            #         'date_end':'2015-02-27'
            #     }
            # ]
        }

        # update multi currency prices
        if doc_oc_product.multi_currency_price:
            prices = []
            for currency_code, price_field_name in CURRENCY_TO_PRICE_FIELD_MAP.items():
                prices.append({
                    'price': str(doc_oc_product.get(price_field_name)) if doc_oc_product.get(price_field_name) is not None else '',
                    'code': currency_code,
                })
            data.update({
                'prices': prices
            })

        # specials
        product_special = []
        for doc_oc_special in doc_item.oc_specials:
            if cur_site_name != doc_oc_special.get('oc_site'):
                continue
            doc_customer_group = frappe.get_doc('Customer Group', doc_oc_special.get('customer_group'))
            customer_group_id = doc_customer_group.get('oc_customer_group_id')
            if not customer_group_id:
                continue
            if cur_site_name != doc_customer_group.get('oc_site'):
                frappe.throw('Customer Group "%s" does not exist in Opencart site "%s"' % (doc_customer_group.get('name'), cur_site_name))
            product_special.append({
                'customer_group_id': customer_group_id,
                'price': doc_oc_special.price,
                'priority': doc_oc_special.priority,
                'date_start': getdate(doc_oc_special.date_start).strftime("%Y-%m-%d") if doc_oc_special.date_start else '',
                'date_end': getdate(doc_oc_special.date_end).strftime("%Y-%m-%d") if doc_oc_special.date_end else '',
            })
        data['product_special'] = product_special

        # discounts
        product_discount = []
        for doc_oc_discount in doc_item.oc_discounts:
            if cur_site_name != doc_oc_discount.get('oc_site'):
                continue
            doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
            customer_group_id = doc_customer_group.get('oc_customer_group_id')
            if not customer_group_id:
                continue
            if cur_site_name != doc_customer_group.get('oc_site'):
                frappe.throw('Customer Group "%s" does not exist in Opencart site "%s"' % (doc_customer_group.get('name'), cur_site_name))
            product_discount_json = {
                'customer_group_id': customer_group_id,
                'price': doc_oc_discount.price,
                'priority': doc_oc_discount.priority,
                'quantity': doc_oc_discount.quantity,
                'date_start': getdate(doc_oc_discount.date_start).strftime("%Y-%m-%d") if doc_oc_discount.date_start else '',
                'date_end': getdate(doc_oc_discount.date_end).strftime("%Y-%m-%d") if doc_oc_discount.date_end else '',
            }
            # update multi currency prices for discount
            if doc_oc_discount.multi_currency_price:
                prices = []
                for currency_code, price_field_name in CURRENCY_TO_PRICE_FIELD_MAP.items():
                    prices.append({
                        'price': str(doc_oc_discount.get(price_field_name)) if doc_oc_discount.get(price_field_name) is not None else '',
                        'code': currency_code,
                    })
                product_discount_json.update({
                    'prices': prices
                })
            product_discount.append(product_discount_json)

        data['product_discount'] = product_discount

        # updating or creating product
        if oc_product_id and get_product_success:
            # update existed product on Opencart site
            success = oc_api.get(cur_site_name).update_product(oc_product_id, data)
            if success:
                frappe.msgprint('Product is updated successfully on Opencart site "%s"' % cur_site_name)
                doc_oc_product.update({'oc_last_sync_to': datetime.now()})
            else:
                frappe.msgprint('Product is not updated on Opencart site "%s". Error: Unknown' % cur_site_name)
        else:
            # add new product on Opencart site
            success, product_id = oc_api.get(cur_site_name).create_product(data)
            if success:
                doc_oc_product.update({
                    'oc_product_id': product_id,
                    'oc_last_sync_to': datetime.now()
                })
                frappe.msgprint('Product is created successfully on Opencart site "%s"' % cur_site_name)
            else:
                frappe.msgprint('Product is not created on Opencart site "%s". Error: Unknown' % cur_site_name)


@sync_item_to_opencart
def oc_validate(self, method=None):
    if self.get("__islocal"):
        return
    sync_item_to_oc(self.item_code, self)


@sync_item_to_opencart
def oc_delete(self, method=None):
    for doc_oc_product in self.get('oc_products'):
        if not doc_oc_product.get('oc_sync_to'):
            continue
        site_name = doc_oc_product.get('oc_site')
        oc_product_id = doc_oc_product.get('oc_product_id')
        success = oc_api.get(site_name).delete_product(oc_product_id)
        if success:
            frappe.msgprint('Product was deleted successfully on Opencart site "%s"' % site_name)
        else:
            frappe.throw('Product is not deleted on Opencart site "%s". Error: Unknown' % site_name)


@sync_item_to_opencart
def push_image(doc):
    if not doc.image:
        return
    site_name = doc.get('oc_site')
    image_file_data = frappe.get_doc('File', {
        'file_url': doc.image,
        'attached_to_doctype': 'Item',
        'attached_to_name': doc.get('name')
    })
    if not image_file_data:
        frappe.throw('Cannot find image in file path "%s"' % doc.image)
    file_name = image_file_data.get('file_name')
    file_path = get_files_path() + '/' + file_name
    oc_product_id = doc.get('oc_product_id')
    success = oc_api.get(site_name).set_product_image(oc_product_id, file_path)
    if success:
        frappe.msgprint('Image "%s" was uploaded successfully to Opencart site' % file_name)
    else:
        frappe.msgprint('Image "%s" was not uploaded to Opencart site' % file_name)


def get_item(site_name, oc_product_id):
    db_item = frappe.db.get('Item', {'oc_site': site_name, 'oc_product_id': oc_product_id})
    if db_item:
        return frappe.get_doc('Item', db_item.get('name'))


def get_item_by_item_code(item_code):
    db_item = frappe.db.get('Item', {'item_code': item_code.upper()})
    if db_item:
        return frappe.get_doc('Item', db_item.get('name'))


def get_opencart_product(site_name, item_name):
    db_item = frappe.db.get('Opencart Product', {'oc_site': site_name, 'parent': item_name})
    if db_item:
        return frappe.get_doc('Opencart Product', {'oc_site': site_name, 'parent': item_name})


def update_discount_price(doc_oc_discount, currency, price):
    doc_oc_discount.update({get_price_field_name(currency): price})


def update_discount_prices(doc_oc_discount, oc_discount):
    doc_oc_discount.update({'price': oc_discount.get('price')})
    if oc_discount.get('prices'):
        if not oc_discount.get('multi_currency_price_unknown'):
            # update multi_currency_price flag only in the case oc_discount is from Opencart
            doc_oc_discount.update({'multi_currency_price': 1})
        for prouct_price in oc_discount.get('prices'):
            update_discount_price(doc_oc_discount, prouct_price.get('code'), float(prouct_price.get('price', 0)))


def update_or_create_item_discount(site_name, doc_item, oc_discount, save=False, is_updating=False):
    disc_template = '{customer_group_id}-{quantity}-{priority}-{date_start}-{date_end}'

    oc_discount_copy = dict(oc_discount)
    oc_discount_copy.update({
        'date_start': parse_date(str(oc_discount.get('date_start'))) if oc_discount.get('date_start') else '',
        'date_end': parse_date(str(oc_discount.get('date_end'))) if oc_discount.get('date_end') else ''
    })
    oc_discount_hash = disc_template.format(**oc_discount_copy)
    for doc_oc_discount in doc_item.get('oc_discounts'):
        if site_name != doc_oc_discount.get('oc_site'):
            continue
        doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
        if site_name != doc_customer_group.get('oc_site'):
            continue
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        if not customer_group_id:
            frappe.throw('customer_group_id is not set in Customer Group "%s"' % doc_oc_discount.get('customer_group'))
        doc_discount_hash = disc_template.format(**{
            'customer_group_id': customer_group_id,
            # 'price': doc_oc_discount.get('price'),
            'priority': int(doc_oc_discount.get('priority', 0)),
            'quantity': int(doc_oc_discount.get('quantity', 0)),
            'date_start': parse_date(str(doc_oc_discount.get('date_start'))) if doc_oc_discount.get('date_start') else '',
            'date_end': parse_date(str(doc_oc_discount.get('date_end'))) if doc_oc_discount.get('date_end') else '',
        })
        if oc_discount_hash == doc_discount_hash:
            update_discount_prices(doc_oc_discount, oc_discount)
            doc_oc_discount.save()
            break
    else:
        doc_customer_group = customer_groups.get(site_name, oc_discount.get('customer_group_id'))
        if not doc_customer_group:
            frappe.throw('Cannot not found Customer Group with customer_group_id "%s" for Item "%s"' % (customer_group_id, doc_item.get('name')))
        doc_oc_discount = frappe.get_doc({
            'doctype': 'Opencart Discount',
            'oc_site': site_name,
            'item_name': doc_item.get('name'),
            'customer_group': doc_customer_group.get('name'),
            'quantity': oc_discount.get('quantity'),
            'priority': oc_discount.get('priority'),
            'price': oc_discount.get('price'),
            'date_start': oc_discount.get('date_start'),
            'date_end': oc_discount.get('date_end'),
        })
        update_discount_prices(doc_oc_discount, oc_discount)
        doc_item.append('oc_discounts', doc_oc_discount)
        if is_updating:
            doc_item.update({'oc_is_updating': 1})
        if save:
            doc_item.save()


def update_or_create_item_discounts(site_name, doc_item, oc_discounts, save=False, is_updating=False):
    for oc_discount in oc_discounts:
        update_or_create_item_discount(site_name, doc_item, oc_discount, save=save, is_updating=is_updating)


def update_opencart_product_price(doc_oc_product, currency, price):
    doc_oc_product.update({get_price_field_name(currency): price})


def update_opencart_product_prices(doc_oc_product, oc_product):
    if oc_product.get('prices'):
        doc_oc_product.update({'multi_currency_price': 1})
        for prouct_price in oc_product.get('prices'):
            update_opencart_product_price(doc_oc_product, prouct_price.get('code'), float(prouct_price.get('price', 0)))


def update_or_create_opencart_product(site_name, doc_item, oc_product, save=False, is_updating=False):
    doc_oc_product = get_opencart_product(site_name, doc_item.get('name'))
    if doc_oc_product:
        doc_oc_product.update({
            'oc_product_id': oc_product.get('product_id'),
            'oc_category_id': oc_product.get('category_id'),
            'oc_manufacturer_id': oc_product.get('manufacturer_id'),
            'oc_tax_class_id': oc_product.get('tax_class_id'),
            'oc_stock_status_id': oc_site.get_stock_status_id_by_name(site_name, oc_product.get('stock_status')),
            'oc_model': oc_product.get('model'),
            'oc_sku': oc_product.get('sku'),
            'oc_quantity': oc_product.get('quantity'),
            'price': oc_product.get('price'),
            'oc_meta_title': oc_product.get('meta_title'),
            'oc_meta_keyword': oc_product.get('meta_keyword'),
            'oc_meta_description': oc_product.get('meta_description'),
            'oc_status': int(oc_product.get('status') or 0),
        })
        update_opencart_product_prices(doc_oc_product, oc_product)
        doc_oc_product.save()
    else:
        doc_oc_product = frappe.get_doc({
            'doctype': 'Opencart Product',
            'oc_site': site_name,
            'oc_product_id': oc_product.get('product_id'),
            'oc_category_id': oc_product.get('category_id'),
            'oc_manufacturer_id': oc_product.get('manufacturer_id') or '',  # not a mandatory field
            'oc_tax_class_id': oc_product.get('tax_class_id'),
            'oc_stock_status_id': oc_site.get_stock_status_id_by_name(site_name, oc_product.get('stock_status')),
            'oc_model': oc_product.get('model'),
            'oc_sku': oc_product.get('sku') or '',  # not a mandatory field
            'oc_quantity': oc_product.get('quantity'),
            'price': oc_product.get('price'),
            'oc_meta_title': oc_product.get('meta_title'),
            'oc_meta_keyword': oc_product.get('meta_keyword'),
            'oc_meta_description': oc_product.get('meta_description'),
            'oc_status': int(oc_product.get('status') or 0),
            'oc_sync_from': 1,
            'oc_sync_to': 1,
        })
        update_opencart_product_prices(doc_oc_product, oc_product)
        doc_item.append('oc_products', doc_oc_product)
        if is_updating:
            doc_item.update({'oc_is_updating': 1})
        if save:
            doc_item.save()


def update_item(site_name, doc_item, oc_product, item_group=None):
    # dec_oc_products = doc_item.get('oc_products')

    # if item_group:
    #     doc_item.update({'item_group': item_group})

    # Opencart product details
    update_or_create_opencart_product(site_name, doc_item, oc_product, save=True, is_updating=True)

    # discounts
    doc_item = frappe.get_doc('Item', doc_item.get('name'))
    update_or_create_item_discounts(site_name, doc_item, oc_product.get('discounts'), save=True, is_updating=True)

    doc_item = frappe.get_doc('Item', doc_item.get('name'))

    # updating item brand
    manufacturer_id = oc_product.get('manufacturer_id')
    if manufacturer_id:
        oc_manufacturer = oc_site.get_manufacturer(site_name, oc_product.get('manufacturer_id'))
        doc_brand = brands.create_or_update(site_name, oc_manufacturer)
        doc_item.update({
            'brand': doc_brand.get('name')
        })
    else:
        frappe.msgprint('Manufacturer is not specified for product "%s" in Opencart site "%s"' % (doc_item.get('name'), site_name))

    doc_item.update({
        'oc_is_updating': 1,
        # update Item general info
        'item_name': oc_product.get('name'),
        'description': oc_product.get('description') or oc_product.get('name'),
        'image': oc_product.get('image'),
        'brand': doc_brand.get('name'),
        #
        'oc_sync_from': 1,
        'oc_last_sync_from': datetime.now(),
        'oc_sync_to': 1,
        'oc_last_sync_to': datetime.now()
    })
    doc_item.save()


@frappe.whitelist()
def pull_from_inventory_spreadsheet(site_name, silent=False):
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    try:
        rows = read_csv_content_from_attached_file(frappe.get_doc("Opencart Site", site_name))
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
        description = row[description_idx]
        if item_code is None or quantity is None or description is None:
            continue
        item_code = item_code.strip().upper()

        check_count += 1
        site_doc = frappe.get_doc('Opencart Site', site_name)
        items_default_warehouse = site_doc.get('items_default_warehouse')
        root_item_group = site_doc.get('root_item_group')
        if not items_default_warehouse:
            sync_info([], 'Please specify a Default Warehouse and proceed.', stop=True, silent=silent)

        doc_item = get_item_by_item_code(item_code)
        if doc_item:
            # update_item(doc_item, oc_product)
            update_count += 1
            extras = (1, 'updated', 'Updated')
            results_list.append((doc_item.get('name'),
                                 doc_item.get('item_group'),
                                 doc_item.get('oc_product_id'),
                                 doc_item.get_formatted('oc_last_sync_from'),
                                 doc_item.get('modified')) + extras)
        else:
            # creating new Item
            params = {
                'doctype': 'Item',
                'item_group': root_item_group,
                'item_code': item_code,
                'is_group': 'No',
                'default_warehouse': items_default_warehouse,
                'item_name': description,
                'description': '',
                'show_in_website': 0,
                'oc_is_updating': 1,
                'oc_site': site_name,
                'oc_product_id': '',
                'oc_manufacturer_id': '',
                'oc_tax_class_id': '',
                'oc_stock_status': '',
                'oc_model': item_code,
                'oc_sku': item_code,
                # 'oc_quantity': quantity,
                'oc_status': 0,
                'oc_meta_title': '',
                'oc_meta_keyword': '',
                'oc_meta_description': '',
                'price': '',
                'oc_sync_from': False,
                'oc_last_sync_from': datetime.now(),
                'oc_sync_to': False,
                'oc_last_sync_to': datetime.now(),
            }
            doc_item = frappe.get_doc(params)
            doc_item.insert(ignore_permissions=True)
            add_count += 1
            extras = (1, 'added', 'Added')
            results_list.append((doc_item.get('name'),
                                root_item_group,
                                doc_item.get('oc_product_id'),
                                doc_item.get_formatted('oc_last_sync_from'),
                                doc_item.get('modified')) + extras)

    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


def pull_product_from_oc(site_name, item_code, doc_item=None):
    if not doc_item:
        doc_item = frappe.get_doc('Item', {"item_code": item_code})

    site_doc = frappe.get_doc('Opencart Site', site_name)
    items_default_warehouse = site_doc.get('items_default_warehouse')
    doc_oc_product = get_opencart_product(site_name, doc_item.get('name'))
    success, oc_product = oc_api.get(site_name).get_product(doc_oc_product.get('oc_product_id'))

    if not success:
        frappe.throw('Cannot get product from Opencart site')

    if doc_item:
        update_item(site_name, doc_item, oc_product)
    else:
        params = {
            'doctype': 'Item',
            'item_code': oc_product.get('model'),
            # 'item_group': doc_item_group.get('name'),
            'is_group': 'No',
            'default_warehouse': items_default_warehouse,
            'item_name': oc_product.get('name'),
            'description': oc_product.get('description'),
            'show_in_website': 1,
            'image': oc_product.get('image'),
            'min_order_qty': oc_product.get('minimum'),
            'oc_is_updating': 1,
            'oc_site': site_name,
            'oc_product_id': oc_product.get('product_id'),
            'oc_manufacturer_id': oc_product.get('manufacturer_id'),
            'oc_tax_class_id': oc_product.get('tax_class_id'),
            'oc_stock_status': oc_product.get('stock_status'),
            'oc_model': oc_product.get('model'),
            'oc_sku': oc_product.get('sku'),
            'oc_quantity': oc_product.get('quantity'),
            'oc_status': int(oc_product.get('status') or 0),
            'oc_meta_title': oc_product.get('meta_title'),
            'oc_meta_keyword': oc_product.get('meta_keyword'),
            'oc_meta_description': oc_product.get('meta_description'),
            'price': oc_product.get('price'),
            'oc_sync_from': True,
            'oc_last_sync_from': datetime.now(),
            'oc_sync_to': True,
            'oc_last_sync_to': datetime.now()
        }
        doc_item = frappe.get_doc(params)
        doc_item.insert(ignore_permissions=True)

        # discounts
        for oc_discount in oc_product.get('discounts'):
            customer_group = customer_groups.get(site_name, oc_discount.get('customer_group_id'))
            if not customer_group:
                continue
            doc_item.append('oc_discounts', {
                'item_name': doc_item.get('name'),
                'customer_group': customer_group.get('name'),
                'quantity': oc_discount.get('quantity'),
                'priority': oc_discount.get('priority'),
                'price': oc_discount.get('price'),
                'date_start': oc_discount.get('date_start'),
                'date_end': oc_discount.get('date_end'),
            })

        # cpesials
        for oc_special in oc_product.get('special'):
            customer_group = customer_groups.get(site_name, oc_special.get('customer_group_id'))
            if not customer_group:
                continue
            doc_item.append('oc_specials', {
                'item_name': doc_item.get('name'),
                'customer_group': customer_group.get('name'),
                'priority': oc_special.get('priority'),
                'price': oc_special.get('price'),
                'date_start': oc_special.get('date_start'),
                'date_end': oc_special.get('date_end'),
            })
        doc_item.update({'oc_is_updating': 1})
        doc_item.save()


@frappe.whitelist()
def pull_products_from_oc(site_name, silent=False):
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    site_doc = frappe.get_doc('Opencart Site', site_name)
    opencart_api = oc_api.get(site_name)
    items_default_warehouse = site_doc.get('items_default_warehouse')
    if not items_default_warehouse:
        sync_info([], 'Please specify a Default Warehouse and proceed.', stop=True, silent=silent)

    for oc_category in opencart_api.get_all_categories():
        oc_category = frappe._dict(oc_category)
        doc_item_group = item_groups.get_item_group(site_name, oc_category.category_id)
        for oc_product in opencart_api.get_products_by_category(oc_category.category_id):
            print("processing oc product: %s" % str(oc_product.get('model')))
            check_count += 1
            item_code = oc_product.get('model', '').upper()
            doc_item = get_item_by_item_code(item_code)

            # skip product if it is disabled on Opencart site
            if not int(oc_product.get('status') or 0):
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: item with Item No. "%s" is disabled on Opencart site' % item_code)
                results_list.append((oc_product.get('name'), '', oc_product.get('product_id'), '', '') + extras)
                continue

            if doc_item_group:
                if doc_item:
                    try:
                        update_item(site_name, doc_item, oc_product, item_group=doc_item_group.get('name'))
                    except Exception as ex:
                        skip_count += 1
                        extras = (1, 'skipped', 'Skipped: due to exception: %s' % str(ex))
                        results_list.append((oc_product.get('name'), '', oc_product.get('product_id'), '', '') + extras)
                        continue

                    update_count += 1
                    extras = (1, 'updated', 'Updated')
                    results_list.append((doc_item.get('name'),
                                         doc_item_group.get('name'),
                                         oc_product.get('product_id'),
                                         doc_item.get_formatted('oc_last_sync_from'),
                                         doc_item.get('modified')) + extras)
                else:
                    skip_count += 1
                    extras = (1, 'skipped', 'Skipped: cannot found item with Item No. "%s"' % item_code)
                    results_list.append((oc_product.get('name'), '', oc_product.get('product_id'), '', '') + extras)
                    continue

                    params = {
                        'doctype': 'Item',
                        'item_code': oc_product.get('model'),
                        'item_group': doc_item_group.get('name'),
                        'is_group': 'No',
                        'default_warehouse': items_default_warehouse,
                        'item_name': oc_product.get('name'),
                        'description': oc_product.get('description'),
                        'show_in_website': 1,
                        'image': oc_product.get('image'),
                        'min_order_qty': oc_product.get('minimum'),
                        'oc_is_updating': 1,
                        'oc_site': site_name,
                        'oc_product_id': oc_product.get('product_id'),
                        'oc_manufacturer_id': oc_product.get('manufacturer_id'),
                        'oc_tax_class_id': oc_product.get('tax_class_id'),
                        'oc_stock_status': oc_product.get('stock_status'),
                        'oc_model': oc_product.get('model'),
                        'oc_sku': oc_product.get('sku'),
                        'oc_quantity': oc_product.get('quantity'),
                        'oc_status': int(oc_product.get('status') or 0),
                        'oc_meta_title': oc_product.get('meta_title'),
                        'oc_meta_keyword': oc_product.get('meta_keyword'),
                        'oc_meta_description': oc_product.get('meta_description'),
                        'price': oc_product.get('price'),
                        'oc_sync_from': True,
                        'oc_last_sync_from': datetime.now(),
                        'oc_sync_to': True,
                        'oc_last_sync_to': datetime.now()
                    }
                    doc_item = frappe.get_doc(params)
                    doc_item.insert(ignore_permissions=True)

                    # discounts
                    for oc_discount in oc_product.get('discounts'):
                        customer_group = customer_groups.get(site_name, oc_discount.get('customer_group_id'))
                        if not customer_group:
                            continue
                        doc_item.append('oc_discounts', {
                            'item_name': doc_item.get('name'),
                            'customer_group': customer_group.get('name'),
                            'quantity': oc_discount.get('quantity'),
                            'priority': oc_discount.get('priority'),
                            'price': oc_discount.get('price'),
                            'date_start': oc_discount.get('date_start'),
                            'date_end': oc_discount.get('date_end'),
                        })

                    # cpesials
                    for oc_special in oc_product.get('special'):
                        customer_group = customer_groups.get(site_name, oc_special.get('customer_group_id'))
                        if not customer_group:
                            continue
                        doc_item.append('oc_specials', {
                            'item_name': doc_item.get('name'),
                            'customer_group': customer_group.get('name'),
                            'priority': oc_special.get('priority'),
                            'price': oc_special.get('price'),
                            'date_start': oc_special.get('date_start'),
                            'date_end': oc_special.get('date_end'),
                        })
                    doc_item.update({'oc_is_updating': 1})
                    doc_item.save()
                    add_count += 1
                    extras = (1, 'added', 'Added')
                    results_list.append((doc_item.get('name'),
                                        doc_item_group.get('name'),
                                        oc_product.get('product_id'),
                                        doc_item.get_formatted('oc_last_sync_from'),
                                        doc_item.get('modified')) + extras)
            else:
                skip_count += 1
                extras = (1, 'skipped', 'Skipped: missed parent category')
                results_list.append((oc_product.get('name'), '', oc_product.get('product_id'), '', '') + extras)

    results = {
        'check_count': check_count,
        'add_count': add_count,
        'update_count': update_count,
        'skip_count': skip_count,
        'results': results_list,
        'success': success,
    }
    return results


@frappe.whitelist()
def sync_item_from_oc(item_code):
    doc_item = frappe.get_doc("Item", {"item_code": item_code})
    if not doc_item.oc_sync_from:
        frappe.throw("Please enable \"{}\" option in Item settings and try again.".format(doc_item.meta.get_label("oc_sync_from")))
    for doc_oc_product in doc_item.oc_products:
        pull_product_from_oc(doc_oc_product.oc_site, item_code)


@frappe.whitelist()
def get_manufacturer_names(site_name, filter_name):
    manufacturer_names = [manufacturer.get("name") for manufacturer in oc_site.get_manufacturers(site_name)]
    if filter_name:
        return filter(lambda name: name.upper().startswith(filter_name.upper()), manufacturer_names) or []
    return manufacturer_names


@frappe.whitelist()
def get_manufacturer_id(site_name, name):
    manufacturers = oc_site.get_manufacturers(site_name) or []
    return next((manufacturer.get("manufacturer_id") for manufacturer in manufacturers if manufacturer.get("name").upper() == name.upper()), None)


@frappe.whitelist()
def get_category_id(site_name, name):
    categories = oc_site.get_all_categories()[site_name] or []
    return next((category.category_id for category in categories if category.name.upper() == name.upper()), None)


@frappe.whitelist()
def get_stock_status_names(site_name, filter_name):
    stock_status_names = [stock_status.get("name") for stock_status in oc_site.get_oc_init(site_name).get("stock_statuses", [])]
    if filter_name:
        return filter(lambda name: name.upper().startswith(filter_name.upper()), stock_status_names) or []
    return stock_status_names


@frappe.whitelist()
def get_stock_status_id(site_name, name):
    stock_statuses = oc_site.get_oc_init(site_name).get("stock_statuses", [])
    return next((stock_status.get("stock_status_id") for stock_status in stock_statuses if stock_status.get("name").upper() == name.upper()), None)


@frappe.whitelist()
def get_tax_class_names(site_name, filter_name):
    oc_items = frappe.get_all("Opencart Product", fields=["name", "oc_tax_class_name", "oc_tax_class_id"], filters={"oc_site": site_name})
    tax_classes = {oc_item.oc_tax_class_id: oc_item for oc_item in oc_items}.values()
    tax_class_names = [oc_item.oc_tax_class_name for oc_item in tax_classes if oc_item.oc_tax_class_name]
    if filter_name:
        return filter(lambda name: name.upper().startswith(filter_name.upper()), tax_class_names) or []
    return tax_class_names


@frappe.whitelist()
def get_tax_class_id(site_name, name):
    oc_items = frappe.get_all("Opencart Product", fields=["name", "oc_tax_class_name", "oc_tax_class_id"], filters={"oc_site": site_name}) or []
    return next((oc_item.oc_tax_class_id for oc_item in oc_items if oc_item.oc_tax_class_name.upper() == name.upper()), None)
