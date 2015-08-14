from __future__ import unicode_literals

from frappe.model.document import Document
from erpnext.controllers.print_settings import print_settings_for_item_table


class BackOrderItem(Document):
    def __setup__(self):
        print_settings_for_item_table(self)
