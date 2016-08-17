from datetime import datetime
import json

import frappe
from frappe import _
from frappe.utils import get_files_path, cstr, flt, getdate
from frappe.utils.dateutils import parse_date
from frappe.utils.csvutils import read_csv_content_from_attached_file

from erpnext.stock.get_item_details import get_fuse_available_qty

import oc_api
import oc_site as oc_site_module
import brands
import customer_groups
import item_groups
from decorators import sync_item_to_opencart
from utils import sync_info


def sync_item_to_oc(doc_item, site_name=None):
    return
    item_code = doc_item.item_code
    for doc_oc_product in doc_item.oc_products:
        if not doc_oc_product.oc_sync_to:
            continue
        cur_site_name = doc_oc_product.oc_site
        if site_name and cur_site_name != site_name:
            continue
        get_product_success, oc_product = oc_api.get(cur_site_name).get_product_by_model(item_code)
        oc_product = frappe._dict(oc_product)

        if get_product_success:
            data = oc_product

            # update product_id
            doc_oc_product.oc_product_id = oc_product.id or oc_product.product_id
            doc_oc_product.oc_last_sync_to = datetime.now()

            # update product description
            data['product_description'] = [
                {
                    'language_id': 1,
                    'name': cstr(doc_item.item_name),
                    'description': cstr(doc_item.description),
                    'meta_description': cstr(doc_item.meta_description),
                    'meta_title': cstr(doc_item.meta_title),
                    'meta_keyword': cstr(doc_item.meta_keyword),
                    'tag': cstr(doc_item.product_tag)
                }
            ]

            data['model'] = item_code
            data['sku'] = item_code
            data['keyword'] = doc_item.seo_url
            data['status'] = "0" if doc_item.disabled else data.get("status", "1")

            if "oc_statics" in cstr(doc_item.image):
                data['image'] = doc_item.image
            data['product_category'] = [c.get("category_id") for c in oc_product.get("category", []) if c.get("category_id")]

            # discounts
            not_reset_discounts = oc_product.get("not_reset_discounts") or False
            multi_currency_prices = oc_product.get("multi_currency_prices") or False
            if not_reset_discounts:
                product_discount = oc_product.get("discounts") or []
                product_discount_map = {}
                for d in product_discount:
                    d_hash = "{}-{}-{}".format(
                        cstr(d.get("customer_group_id")).strip(),
                        cstr(d.get("priority")).strip(),
                        cstr(d.get("quantity")).strip())
                    if product_discount_map.get(d_hash):
                        frappe.msgprint("Discounts conflict detected for product on Opencart site {}!".format(cur_site_name))
                    product_discount_map[d_hash] = d

                item_prices = frappe.db.get_all("Item Price", fields=["*"], filters={"item_code": item_code})
                for item_price in item_prices:
                    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': item_price.price_list})
                    if not db_oc_price_list:
                        continue
                    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
                    oc_store_oc_site = db_oc_store.oc_site
                    if doc_oc_product.oc_site != oc_store_oc_site:
                        continue
                    if db_oc_price_list.is_master:
                        if multi_currency_prices:
                            for p in oc_product.get("prices", []) or []:
                                if p.get("code") == item_price.currency:
                                    p["price"] = cstr(item_price.price_list_rate)
                        else:
                            data.update({
                                'price': item_price.price_list_rate
                            })
                    else:
                        db_customer_group = frappe.db.get('Customer Group', {'name': db_oc_price_list.customer_group})
                        if not db_customer_group:
                            frappe.msgprint('Customer Group is not set for Opencart Price List in Opencart Store "{}"'.format(db_oc_store.name))
                            continue
                        customer_group_id = db_customer_group.oc_customer_group_id
                        if customer_group_id:
                            discount_hash = "{}-{}-{}".format(cstr(customer_group_id), '0', '1')
                            oc_discount = product_discount_map.get(discount_hash)
                            if oc_discount:
                                if multi_currency_prices:
                                    oc_discount["price"] = item_price.price_list_rate
                                    for p in oc_discount.get("prices", []) or []:
                                        if p.get("code") == item_price.currency:
                                            p["price"] = cstr(item_price.price_list_rate)
                                else:
                                    oc_discount.update({
                                        'price': item_price.price_list_rate
                                    })
                            else:
                                product_discount.append({
                                    'customer_group_id': customer_group_id,
                                    'price': item_price.price_list_rate,
                                    'priority': '0',
                                    'quantity': '1',
                                    'date_start': '',
                                    'date_end': '',
                                    'prices': [{
                                        'code': item_price.currency,
                                        'price': item_price.price_list_rate
                                    }]
                                })
            else:
                product_discount = []
                item_prices = frappe.db.get_all("Item Price", fields=["*"], filters={"item_code": item_code})
                for item_price in item_prices:
                    db_oc_price_list = frappe.db.get('Opencart Price List', {'price_list': item_price.price_list})
                    if not db_oc_price_list:
                        continue
                    db_oc_store = frappe.db.get(db_oc_price_list.get('parenttype'), db_oc_price_list.get('parent'))
                    oc_store_oc_site = db_oc_store.oc_site
                    if doc_oc_product.oc_site != oc_store_oc_site:
                        continue
                    if db_oc_price_list.is_master:
                        data.update({
                            'price': item_price.price_list_rate,
                            'prices': [{
                                'code': item_price.currency,
                                'price': item_price.price_list_rate
                            }]
                        })
                    else:
                        db_customer_group = frappe.db.get('Customer Group', {'name': db_oc_price_list.customer_group})
                        if not db_customer_group:
                            frappe.msgprint('Customer Group is not set for Opencart Price List in Opencart Store "{}"'.format(db_oc_store.name))
                            continue
                        customer_group_id = db_customer_group.oc_customer_group_id
                        if customer_group_id:
                            product_discount.append({
                                'customer_group_id': customer_group_id,
                                'price': item_price.price_list_rate,
                                'priority': '0',
                                'quantity': '1',
                                'date_start': '',
                                'date_end': '',
                                'prices': [{
                                    'code': item_price.currency,
                                    'price': item_price.price_list_rate
                                }]
                            })
            data['product_discount'] = product_discount

        elif get_product_success is False:
            data = {
                'model': item_code,
                'sku': item_code,
                'keyword': doc_item.seo_url,
                # 'quantity': 1000,
                # 'price': 100,
                # 'tax_class_id': 13,
                # 'manufacturer_id': 12,
                'status': "0" if doc_item.disabled else "1",
                # 'stock_status_id': 7,

                # # 'quantity': doc_oc_product.get('oc_quantity') or '0',  # mandatory
                # 'price': doc_oc_product.get('price'),
                # 'tax_class_id': doc_oc_product.get('oc_tax_class_id'),  # mandatory
                # 'manufacturer_id': doc_oc_product.get('oc_manufacturer_id'),  # mandatory
                # # 'sort_order': '1',  # mandatory
                # 'status': doc_oc_product.get('oc_status'),
                # # ,
                # # 'upc': '',
                # # 'ean': '',
                # # 'jan': '',
                # # 'isbn': '',
                # # 'mpn': '',
                # # 'location': '',
                # 'stock_status_id': doc_oc_product.get('oc_stock_status_id'),

                # 'reward': '400',
                # 'points': '200',
                'image': doc_item.image,
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
                'product_description': [
                    {
                        'language_id': 1,
                        'name': cstr(doc_item.item_name),
                        'description': cstr(doc_item.description),
                        'meta_description': cstr(doc_item.meta_description),
                        'meta_title': cstr(doc_item.meta_title),
                        'meta_keyword': cstr(doc_item.meta_keyword),
                        'tag': cstr(doc_item.product_tag)
                    }
                ]
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
        else:
            frappe.msgprint('Skipping product update on Opencart site {}. Error: cannot get product by model {}'.format(cur_site_name, item_code))
            continue

        if doc_oc_product.product_details_to_update and isinstance(doc_oc_product.product_details_to_update, basestring):
            pd = frappe._dict(json.loads(doc_oc_product.product_details_to_update))
            if pd:
                pd_to_update = {}

                # manufacturer_id
                manufacturer_id = get_manufacturer_id(cur_site_name, pd.manufacturer)
                if manufacturer_id not in (None, ""):
                    pd_to_update["manufacturer_id"] = manufacturer_id

                # product_category
                product_category = []
                for category_name in cstr(pd.category_names).split(","):
                    category_id = get_category_id(cur_site_name, category_name)
                    if category_id not in (None, ""):
                        product_category.append(category_id)
                pd_to_update["product_category"] = product_category

                # product_store
                product_store = []
                for store_name in cstr(pd.store_names).split(","):
                    store_id = get_store_id(cur_site_name, store_name)
                    if store_id not in (None, ""):
                        product_store.append(store_id)
                pd_to_update["product_store"] = product_store

                # product_attributes
                product_attributes = []
                for attribute_value in pd.attributes_values:
                    attribute_name = cstr(attribute_value.get("name")).strip()
                    attribute_text = cstr(attribute_value.get("text")).strip()
                    if attribute_name and attribute_text:
                        attribute = get_attribute(cur_site_name, attribute_name)
                        if attribute:
                            attribute["text"] = attribute_text
                            product_attributes.append(attribute)
                pd_to_update["product_attribute"] = product_attributes

                # status
                pd_to_update["status"] = "0" if doc_item.disabled else pd.status

                # tax_class_id
                pd_to_update["tax_class_id"] = pd.tax_class_id

                # frappe.msgprint(cstr(doc_oc_product.product_details_to_update))
                doc_oc_product.product_details_to_update = None
                data.update(pd_to_update)

        # update actual qty and stock status
        available_qty = get_fuse_available_qty(item_code, frappe.db.get_value("Opencart Site", cur_site_name, "default_warehouse"))
        actual_qty = flt(available_qty.actual_qty)
        stock_status_id = get_stock_status_id(cur_site_name, "In Stock") if actual_qty else get_stock_status_id(cur_site_name, "Out Of Stock")
        data.update({
            "quantity": actual_qty,
            "stock_status_id": stock_status_id
        })

        # updating or creating product
        if get_product_success:
            # update existed product on Opencart site
            success, resp = oc_api.get(cur_site_name).update_product(doc_oc_product.oc_product_id, data)
            if success:
                frappe.msgprint('Product is updated successfully on Opencart site {}'.format(cur_site_name))
                doc_oc_product.update({'oc_last_sync_to': datetime.now()})
            else:
                frappe.msgprint('Product is not updated on Opencart site {}. Error: {}'.format(cur_site_name, resp.get("error")))
        elif get_product_success is False:
            # add new product on Opencart site
            success, product_id = oc_api.get(cur_site_name).create_product(data)
            if success:
                # update product_id
                doc_oc_product.oc_product_id = product_id
                doc_oc_product.oc_last_sync_to = datetime.now()

                frappe.msgprint('Product is created successfully on Opencart site {}'.format(cur_site_name))
            else:
                frappe.msgprint('Product is not created on Opencart site {}. Error: Unknown'.format(cur_site_name))
        else:
            frappe.msgprint('Product is not updated on Opencart site {}. Error: cannot get product by model {}'.format(cur_site_name, item_code))


def _on_bin_update(bin_name, actual_qty_diff):
    return
    bin_doc = frappe.get_doc("Bin", bin_name)
    oc_products = frappe.db.get_all("Opencart Product", filters={"parent": bin_doc.item_code}, fields=["parent", "name", "oc_site", "oc_product_id", "oc_category_id", "oc_manufacturer_id", "oc_stock_status_id", "oc_category_name", "oc_manufacturer_name", "oc_stock_status_name"])
    for pr in oc_products:
        item_code = pr.parent
        oc_site = pr.oc_site
        warehouse = frappe.db.get_value("Opencart Site", oc_site, "default_warehouse")
        if warehouse != bin_doc.warehouse:
            continue
        success, oc_product = oc_api.get(oc_site).get_product_by_model(item_code)
        if success:
            available_qty = get_fuse_available_qty(item_code, warehouse)
            actual_qty = flt(available_qty.actual_qty) + actual_qty_diff
            update_success, resp = oc_api.get(oc_site).update_product_quantity([{
                "product_id": oc_product.get("product_id") or oc_product.get("id"),
                "quantity": cstr(actual_qty),
                "stock_status_name": "In Stock" if actual_qty else "Out Of Stock"
            }])
            if not update_success:
                frappe.msgprint("Stock quantity for {} item is not uptated on Opencart site {}".format(item_code, oc_site))
        else:
            pass


def on_bin_update(self, method=None):
    return
    db_actual_qty = flt(frappe.db.get_value("Bin", self.name, "actual_qty"))
    if self.get("__islocal") or flt(self.actual_qty) == db_actual_qty:
        return

    actual_qty_diff = flt(self.actual_qty) - db_actual_qty
    if getattr(frappe.local, "is_ajax", False):
        from tasks import on_bin_update_task
        on_bin_update_task.delay(frappe.local.site, self.name, actual_qty_diff, event="bulk_long")
    else:
        return _on_bin_update(self.name, actual_qty_diff)


@sync_item_to_opencart
def oc_validate(self, method=None):
    return
    # delete producs from Opencart site
    if not self.get("__islocal"):
        item_doc = frappe.get_doc("Item", self.item_code)
        oc_products_now = [p.name for p in self.oc_products]
        for p in item_doc.oc_products:
            if p.name not in oc_products_now:
                on_trash_oc_product(p)

    # sync item to Opencart site
    sync_item_to_oc(self)


@sync_item_to_opencart
def on_trash_oc_product(oc_product_doc):
    return
    if not oc_product_doc.oc_sync_to:
        return
    oc_site = oc_product_doc.oc_site
    oc_product_id = oc_product_doc.oc_product_id
    success, resp = oc_api.get(oc_site).delete_product(oc_product_id)
    if success:
        frappe.msgprint('Product was deleted successfully on Opencart site "{}"'.format(oc_site))
    else:
        frappe.throw('Product is not deleted on Opencart site "{}". Error: {}'.format(oc_site, resp.get("error")))


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


def update_or_create_opencart_product(site_name, doc_item, oc_product, save=False, is_updating=False):
    doc_oc_product = get_opencart_product(site_name, doc_item.get('name'))
    if doc_oc_product:
        doc_oc_product.update({
            'oc_product_id': oc_product.get('product_id'),
        })
        doc_oc_product.save()
    else:
        doc_oc_product = frappe.get_doc({
            'doctype': 'Opencart Product',
            'oc_site': site_name,
            'oc_product_id': oc_product.get('product_id'),
            'oc_sync_from': 1,
            'oc_sync_to': 1,
        })
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

    doc_item = frappe.get_doc('Item', doc_item.get('name'))

    # updating item brand
    manufacturer_id = oc_product.get('manufacturer_id')
    if manufacturer_id:
        oc_manufacturer = oc_site_module.get_manufacturer(site_name, oc_product.get('manufacturer_id'))
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
        default_warehouse = site_doc.get('default_warehouse')
        root_item_group = site_doc.get('root_item_group')
        if not default_warehouse:
            sync_info([], 'Please specify a Default Warehouse and proceed.', stop=True, silent=silent)

        doc_item = get_item_by_item_code(item_code)
        if doc_item:
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
                'default_warehouse': default_warehouse,
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
    return
    if not doc_item:
        doc_item = frappe.get_doc('Item', {"item_code": item_code})

    site_doc = frappe.get_doc('Opencart Site', site_name)
    default_warehouse = site_doc.get('default_warehouse')
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
            'default_warehouse': default_warehouse,
            'item_name': oc_product.get('name'),
            'description': oc_product.get('description'),
            'show_in_website': 1,
            'image': oc_product.get('image'),
            'min_order_qty': oc_product.get('minimum'),
            'oc_is_updating': 1,
            'oc_model': oc_product.get('model'),
            'oc_sku': oc_product.get('sku'),
            'oc_meta_title': oc_product.get('meta_title'),
            'oc_meta_keyword': oc_product.get('meta_keyword'),
            'oc_meta_description': oc_product.get('meta_description'),
            'oc_sync_from': True,
            'oc_last_sync_from': datetime.now(),
            'oc_sync_to': True,
            'oc_last_sync_to': datetime.now()
        }
        doc_item = frappe.get_doc(params)
        doc_item.insert(ignore_permissions=True)


@frappe.whitelist()
def pull_products_from_oc(site_name, silent=False):
    return
    results = {}
    results_list = []
    check_count = 0
    update_count = 0
    add_count = 0
    skip_count = 0
    success = True

    site_doc = frappe.get_doc('Opencart Site', site_name)
    opencart_api = oc_api.get(site_name)
    default_warehouse = site_doc.get('default_warehouse')
    if not default_warehouse:
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
                        'default_warehouse': default_warehouse,
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
def get_manufacturer_names(site_name, filter_term=None):
    manufacturer_names = [manufacturer.get("name") for manufacturer in oc_site_module.get_manufacturers(site_name)]
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), manufacturer_names) or []
    return manufacturer_names


@frappe.whitelist()
def get_manufacturer_id(site_name, name):
    if not name:
        return None
    manufacturers = oc_site_module.get_manufacturers(site_name) or []
    return next((manufacturer.get("manufacturer_id") for manufacturer in manufacturers if cstr(manufacturer.get("name")).strip() == cstr(name).strip()), None)


@frappe.whitelist()
def get_category_names(site_name, filter_term=None):
    category_names = [category.get("name") for category in oc_site_module.get_categories(site_name)]
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), category_names) or []
    return category_names


@frappe.whitelist()
def get_category_id(site_name, name):
    if not name:
        return None
    categories = oc_site_module.get_categories(site_name) or []
    return next((category.get("category_id") for category in categories if cstr(category.get("name")).strip() == cstr(name).strip()), None)


@frappe.whitelist()
def get_store_names(site_name, filter_term=None):
    store_names = [store.get("name") for store in oc_site_module.get_oc_init(site_name).get("stores", [])]
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), store_names) or []
    return store_names


@frappe.whitelist()
def get_store_id(site_name, name):
    if not name:
        return None
    stores = oc_site_module.get_oc_init(site_name).get("stores", [])
    return next((store.get("store_id") for store in stores if store.get("name").upper() == name.upper()), None)


@frappe.whitelist()
def get_stock_status_names(site_name, filter_term=None):
    stock_status_names = [stock_status.get("name") for stock_status in oc_site_module.get_oc_init(site_name).get("stock_statuses", [])]
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), stock_status_names) or []
    return stock_status_names


@frappe.whitelist()
def get_stock_status_id(site_name, name):
    if not name:
        return None
    stock_statuses = oc_site_module.get_oc_init(site_name).get("stock_statuses", [])
    return next((stock_status.get("stock_status_id") for stock_status in stock_statuses if stock_status.get("name").upper() == name.upper()), None)


@frappe.whitelist()
def get_tax_classes(site_name, filter_term=None):
    oc_items = frappe.get_all("Opencart Product", fields=["name", "oc_tax_class_name", "oc_tax_class_id"], filters={"oc_site": site_name})
    tax_classes = {oc_item.oc_tax_class_id: oc_item for oc_item in oc_items}.values()
    tax_class_names = [oc_item.oc_tax_class_name for oc_item in tax_classes if oc_item.oc_tax_class_name]
    tax_class_names = list(set(tax_class_names))
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), tax_class_names) or []
    return tax_class_names


@frappe.whitelist()
def get_tax_class_names(site_name, filter_term=None):
    oc_items = frappe.get_all("Opencart Product", fields=["name", "oc_tax_class_name", "oc_tax_class_id"], filters={"oc_site": site_name})
    tax_classes = {oc_item.oc_tax_class_id: oc_item for oc_item in oc_items}.values()
    tax_class_names = [oc_item.oc_tax_class_name for oc_item in tax_classes if oc_item.oc_tax_class_name]
    tax_class_names = list(set(tax_class_names))
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), tax_class_names) or []
    return tax_class_names


@frappe.whitelist()
def get_tax_class_id(site_name, name):
    if not name:
        return None
    oc_items = frappe.get_all("Opencart Product", fields=["name", "oc_tax_class_name", "oc_tax_class_id"], filters={"oc_site": site_name})
    return next((oc_item.oc_tax_class_id for oc_item in oc_items if oc_item.oc_tax_class_name and oc_item.oc_tax_class_name.upper() == name.upper()), None)


@frappe.whitelist()
def get_attribute_names(site_name, filter_term=None):
    attribute_names = [attribute.get("name") for attribute in oc_site_module.get_attributes(site_name)]
    if filter_term:
        return filter(lambda name: name.upper().startswith(filter_term.upper()), attribute_names) or []
    return attribute_names


@frappe.whitelist()
def get_attribute(site_name, name):
    if not name:
        return None
    attributes = oc_site_module.get_attributes(site_name) or []
    return next((attribute for attribute in attributes if cstr(attribute.get("name")).strip() == cstr(name).strip()), None)


@frappe.whitelist()
def get_attribute_id(site_name, name):
    if not name:
        return None
    attributes = oc_site_module.get_attributes(site_name) or []
    return next((attribute.get("attribute_id") for attribute in attributes if cstr(attribute.get("name")).strip() == cstr(name).strip()), None)


@frappe.whitelist()
def get_oc_products_raw(item_code):
    oc_products_raw = {}
    oc_products = frappe.db.get_all("Opencart Product", fields=["name", "oc_site"], filters={"parent": item_code})
    for p in oc_products:
        oc_site = p.oc_site
        try:
            init_data = oc_site_module.get_oc_init(oc_site)
            product_details = {"success": False, "oc_product": {}, "oc_product_calculated": {}}
            get_product_success, oc_product = oc_api.get(oc_site).get_product_by_model(item_code)
            if get_product_success:
                product_details["success"] = True
                product_details["oc_product"] = oc_product
                calculated = {
                    "category_names": ",".join([c.get("name") for c in oc_product.get("category", []) if c.get("name")])
                }

                store_names = []
                for store in init_data.get("stores", []):
                    if cstr(store.get("store_id")) in [cstr(store_id) for store_id in oc_product.get("product_store", [])]:
                        store_names.append(store.get("name"))
                calculated["store_names"] = store_names

                product_details["oc_product_calculated"] = calculated

            product_details["manufacturer_names"] = get_manufacturer_names(oc_site)
            product_details["category_names"] = get_category_names(oc_site)
            product_details["stock_status_names"] = get_stock_status_names(oc_site)
            product_details["attribute_names"] = get_attribute_names(oc_site)
            product_details["store_names"] = [cstr(store.get("name")) for store in init_data.get("stores", [])]
            product_details["init_data"] = init_data

            oc_products_raw[oc_site] = product_details
        except Exception as ex:
            frappe.msgprint("Cannot get product for Opencart Site {}. Error {}".format(oc_site, cstr(ex)))
    return oc_products_raw
