from __future__ import unicode_literals

from frappe.utils import cstr


class ItemGroups(object):
    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.category_id)


class OpencartCategory(object):
    obj_attrs = ('id', 'category_id', 'name', 'description', 'image',
                 'sort_order', 'meta_title', 'meta_description',
                 'meta_keyword', 'language_id', 'categories')

    def __init__(self, oc_api, attrs, level=None, parent=None):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        setattr(self, 'level', cstr(level) if level else '')
        setattr(self, 'parent_id', cstr(parent) if parent else '')
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.category_id)


class OpencartProductOption(object):
    obj_attrs = ('id', 'option_id', 'name', 'sort_order', 'option_values')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.option_id)

    @property
    def option_values_list(self):
        return [OpencartProductOptionValue(self.api, ov) for ov in self.option_values] if self.option_values else []

    def __repr__(self):
        return '%s - %s' % (self.id, self.name)


class OpencartProductOptionValue(object):
    obj_attrs = ('id', 'option_value_id', 'option_value_description', 'name', 'language_id', 'image', 'thumb', 'sort_order')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.option_value_id)
        for description in self.option_value_description.values():
            # name, language_id
            for attr in description:
                setattr(self, attr, description[attr])
            break

    def __repr__(self):
        return '%s - %s' % (self.id, self.name)


class OpencartProductOptionExt(object):
    obj_attrs = ('id', 'name', 'type', 'option_value', 'option_id', 'required', 'product_option_id')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.option_id)

    @property
    def option_values_list(self):
        return [OpencartProductOptionValueExt(self.api, ov) for ov in self.option_value] if self.option_value else []

    def __repr__(self):
        return '%s - %s' % (self.id, self.name)


class OpencartProductOptionValueExt(object):
    obj_attrs = ('id', 'image', 'price', 'price_formated', 'price_prefix', 'product_option_value_id', 'option_value_id', 'name', 'quantity')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.option_value_id)

    def __repr__(self):
        return '%s - %s' % (self.id, self.name)


class OpencartStore(object):
    obj_attrs = ('store_id', 'name')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', cstr(self.store_id))

    def __repr__(self):
        return '%s - %s' % (self.id, self.name)


class OpencartCustomerGroup(object):
    obj_attrs = ('customer_group_id', 'name', 'sort_order', 'description', 'language_id')

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.customer_group_id)

    def __repr__(self):
        return 'customer_group_id %s' % (self.id,)


# class OpencartCustomer(object):
#     obj_attrs = ('store_id', 'customer_id', 'firstname', 'lastname',
#                  'telephone', 'fax', 'email', 'account_custom_field', 'custom_fields')

#     def __init__(self, oc_api, attrs):
#         self.api = oc_api
#         for attr in attrs.keys():
#             setattr(self, attr, attrs[attr])
#         self._fixup()

#     def _fixup(self):`
#         setattr(self, 'id', self.customer_id)
#         setattr(self, 'name', self.firstname + ' ' + self.lastname)

#     def __repr__(self):
#         return 'customer_id %s' % (self.id,)


class OpencartOrder(object):
    # obj_attrs = ('order_id',...)

    def __init__(self, oc_api, attrs):
        self.api = oc_api
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])
        self._fixup()

    def _fixup(self):
        setattr(self, 'id', self.order_id)

    def __repr__(self):
        return 'order_id %s' % (self.id,)
