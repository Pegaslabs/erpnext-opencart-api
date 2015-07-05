from datetime import datetime

import frappe
from frappe.utils import get_files_path
from frappe.utils import cstr

import oc_api
import oc_site
import customer_groups
import item_groups
import item_attributes
from decorators import sync_to_opencart
from utils import sync_info


@sync_to_opencart
def oc_validate(doc, method=None):
    site_name = doc.get('oc_site')
    item_group_name = doc.get('item_group')
    valid_group_names = [item_group.get('name') for item_group in item_groups.get_all_by_oc_site(site_name) if item_group.get('oc_category_id')]
    if item_group_name not in valid_group_names:
        frappe.throw('To sync Item to Opencart Site, Item Group must be one of the following:\n%s' % cstr(', '.join(valid_group_names)))
    doc_item_group = frappe.get_doc('Item Group', item_group_name)
    doc.update({'oc_sku': doc.get('oc_sku') or doc.get('name')})

    data = {
        'model': doc.get('oc_model') or doc.get('name'),  # mandatory
        'sku': doc.get('oc_sku'),  # mandatory
        'quantity': doc.get('oc_quantity') or '0',  # mandatory
        'price': doc.get('oc_price'),
        'tax_class_id': doc.get('oc_tax_class_id'),  # mandatory
        'manufacturer_id': doc.get('oc_manufacturer_id'),  # mandatory
        # 'sort_order': '1',  # mandatory
        'status': doc.get('oc_status'),
        # ,
        # 'upc': '',
        # 'ean': '',
        # 'jan': '',
        # 'isbn': '',
        # 'mpn': '',
        # 'location': '',
        'stock_status_id': oc_site.get_stock_status_id_by_name(site_name, doc.get('oc_stock_status'))
        # 'reward': '400',
        # 'points': '200',
        # 'image': doc.get('image'),
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
        #         'name': doc.get('item_name'),
        #         'description': doc.get('description_html'),
        #         'meta_description': doc.get('oc_meta_description'),
        #         'meta_title': doc.get('oc_meta_title'),
        #         'meta_keyword': doc.get('oc_meta_keyword'),
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

    # specials
    product_special = []
    for doc_oc_special in doc.oc_specials:
        doc_customer_group = frappe.get_doc('Customer Group', doc_oc_special.get('customer_group'))
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        if not customer_group_id:
            continue
        product_special.append({
            'customer_group_id': customer_group_id,
            'price': doc_oc_special.price,
            'priority': doc_oc_special.priority,
            'date_start': doc_oc_special.date_start,
            'date_end': doc_oc_special.date_end,
        })
    if product_special:
        data['product_special'] = product_special

    # discounts
    product_discount = []
    for doc_oc_discount in doc.oc_discounts:
        doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        if not customer_group_id:
            continue
        product_discount.append({
            'customer_group_id': customer_group_id,
            'price': doc_oc_discount.price,
            'priority': doc_oc_discount.priority,
            'quantity': doc_oc_discount.quantity,
            'date_start': doc_oc_discount.date_start,
            'date_end': doc_oc_discount.date_end,
        })
    if product_discount:
        data['product_discount'] = product_discount

    # updating or creating product
    oc_product_id = doc.get('oc_product_id')
    get_product_success, oc_product = oc_api.get(site_name).get_product(oc_product_id)
    if oc_product_id and get_product_success:
        # update existed product on Opencart site
        success = oc_api.get(site_name).update_product(oc_product_id, data)
        if success:
            frappe.msgprint('Product is updated successfully on Opencart site')
            doc.update({'oc_last_sync_to': datetime.now()})
        else:
            frappe.msgprint('Product is not updated on Opencart site. Error: Unknown')
    else:
        # add new product on Opencart site
        success, product_id = oc_api.get(site_name).create_product(data)
        if success:
            doc.update({
                'oc_product_id': product_id,
                'oc_last_sync_to': datetime.now()
            })
            frappe.msgprint('Product is created successfully on Opencart site')
        else:
            frappe.msgprint('Product is not created on Opencart site. Error: Unknown')


@sync_to_opencart
def oc_delete(doc, method=None):
    site_name = doc.get('oc_site')
    oc_product_id = doc.get('oc_product_id')
    success = oc_api.get(site_name).delete_product(oc_product_id)
    if success:
        frappe.msgprint('Product was deleted successfully on Opencart site')
    else:
        frappe.throw('Product is not deleted on Opencart site. Error: Unknown')


@sync_to_opencart
def push_image(doc):
    if not doc.image:
        return
    site_name = doc.get('oc_site')
    image_file_data = frappe.get_doc('File Data', {
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


def get_all_dict(site_name, fields=['name']):
    return frappe.get_all('Item', fields=fields, filters={'oc_site': site_name})


def update_or_create_item_discount(doc_item, oc_discount, save=False):
    disc_template = '{customer_group_id}-{quantity}-{priority}-{date_start}-{date_end}'
    oc_discount_hash = disc_template.format(**oc_discount)

    for doc_oc_discount in doc_item.get('oc_discounts'):
        doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        if not customer_group_id:
            frappe.throw('customer_group_id is not set in Customer Group "%s"' % doc_oc_discount.get('customer_group'))
        doc_discount_hash = disc_template.format(**{
            'customer_group_id': customer_group_id,
            # 'price': doc_oc_discount.get('price'),
            'priority': int(doc_oc_discount.get('priority', 0)),
            'quantity': int(doc_oc_discount.get('quantity', 0)),
            'date_start': doc_oc_discount.get('date_start') or '',
            'date_end': doc_oc_discount.get('date_end') or '',
        })
        frappe.msgprint('%s = %s' % (oc_discount_hash, doc_discount_hash))
        if oc_discount_hash == doc_discount_hash:
            if doc_oc_discount.get('price') != oc_discount.get('price'):
                doc_oc_discount.update({'price': oc_discount.get('price')})
                doc_oc_discount.save()
            break
    else:
        doc_item.append('oc_discounts', {
            'item_name': doc_item.get('name'),
            'customer_group': doc_customer_group.get('name'),
            'quantity': oc_discount.get('quantity'),
            'priority': oc_discount.get('priority'),
            'price': oc_discount.get('price'),
            'date_start': oc_discount.get('date_start'),
            'date_end': oc_discount.get('date_end'),
        })
    if save:
        doc_item.update({'oc_is_updating': 1})
        doc_item.save()


def update_item_discounts(doc_item, oc_discounts, save=False):
    disc_template = '{customer_group_id}-{quantity}-{priority}-{date_start}-{date_end}'

    oc_discounts_cache = {}
    for discount in oc_discounts:
        k = disc_template.format(**discount)
        oc_discounts_cache[k] = discount

    doc_oc_discounts_cache = {}
    for doc_oc_discount in doc_item.get('oc_discounts'):
        doc_customer_group = frappe.get_doc('Customer Group', doc_oc_discount.get('customer_group'))
        customer_group_id = doc_customer_group.get('oc_customer_group_id')
        if not customer_group_id:
            frappe.throw('customer_group_id is not set in Customer Group "%s"' % doc_oc_discount.get('customer_group'))
        k = disc_template.format(**{
            'customer_group_id': customer_group_id,
            # 'price': doc_oc_discount.get('price'),
            'priority': doc_oc_discount.get('priority'),
            'quantity': doc_oc_discount.get('quantity'),
            'date_start': doc_oc_discount.get('date_start'),
            'date_end': doc_oc_discount.get('date_end'),
        })
        doc_oc_discounts_cache[k] = doc_oc_discount

    # updating discounts
    for k, discount in oc_discounts_cache.items():
        doc_oc_discount = doc_oc_discounts_cache.get(k)
        if doc_oc_discount:
            if doc_oc_discount.get('price') != discount.get('price'):
                doc_oc_discount.update({'price': discount.get('price')})
                doc_oc_discount.save()
        else:
            doc_item.append('oc_discounts', discount)

    if save:
        doc_item.update({'oc_is_updating': 1})
        doc_item.save()


def update_item(doc_item, oc_product, save=False):
    data = {
        'item_name': oc_product.get('name'),
        'description_html': oc_product.get('description'),
        'description': oc_product.get('meta_description'),
        'image': oc_product.get('image'),
        'min_order_qty': oc_product.get('minimum'),
        'oc_is_updating': 1,
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
        'oc_price': oc_product.get('price'),
        'oc_last_sync_from': datetime.now()
    }
    doc_item.update(data)

    # discounts
    doc_item.set('oc_discounts', [])
    for oc_discount in oc_product.get('discounts'):
        customer_group = customer_groups.get(doc_item.get('oc_site'), oc_discount.get('customer_group_id'))
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
    if save:
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
        doc_item_group = item_groups.get_item_group(site_name, oc_category.id)
        for oc_product in opencart_api.get_products_by_category(oc_category.id):
            check_count += 1
            doc_item = get_item(site_name, oc_product.get('product_id'))
            if doc_item_group:
                if doc_item:
                    update_item(doc_item, oc_product)
                    doc_item.save()
                    update_count += 1
                    extras = (1, 'updated', 'Updated')
                    results_list.append((doc_item.get('name'),
                                         doc_item_group.get('name'),
                                         doc_item.get('oc_product_id'),
                                         doc_item.get_formatted('oc_last_sync_from'),
                                         doc_item.get('modified')) + extras)
                else:
                    # creating new Item
                    variants_list = []
                    missed_item_attribute = ''
                    missed_item_attribute_value = ''
                    for option in oc_product.get('options_list'):
                        if missed_item_attribute_value or not item_attributes.get(site_name, option.id):
                            if not missed_item_attribute_value:
                                missed_item_attribute = option.name
                            break
                        for option_value in option.option_values_list:
                            if not item_attributes.get_value(site_name, option_value.id):
                                missed_item_attribute_value = option_value.name
                                break
                            variants_list.append({
                                'item_attribute': option.name,
                                'item_attribute_value': option_value.name
                            })
                    if missed_item_attribute or missed_item_attribute_value:
                        skip_count += 1
                        if missed_item_attribute:
                            skip_msg = 'Skipped: missed item attribute "%s"' % missed_item_attribute
                        else:
                            skip_msg = 'Skipped: missed item attribute value "%s"' % missed_item_attribute_value
                        extras = (1, 'skipped', skip_msg)
                        results_list.append((oc_product.get('name'), doc_item_group.get('name'), oc_product.get('product_id'), '', '') + extras)
                        continue

                    params = {
                        'doctype': 'Item',
                        'item_group': doc_item_group.get('name'),
                        'has_variants': bool(variants_list),
                        'variants': variants_list,
                        'is_group': 'No',
                        'default_warehouse': items_default_warehouse,
                        'item_name': oc_product.get('name'),
                        'description_html': oc_product.get('description'),
                        'description': oc_product.get('meta_description'),
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
                        'oc_price': oc_product.get('price'),
                        'oc_sync_from': True,
                        'oc_last_sync_from': datetime.now(),
                        'oc_sync_to': True,
                        'oc_last_sync_to': datetime.now(),
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
                                        doc_item.get('oc_product_id'),
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
