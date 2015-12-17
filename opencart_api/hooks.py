"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Hooks for Opencart API app
"""

app_name = "opencart_api"
app_title = "Opencart API"
app_publisher = "Nathan (Hoovix Consulting Pte. Ltd.)"
app_description = "App for connecting Opencart through APIs. Updating Products, recording transactions"
app_icon = "icon-book"
app_color = "#589494"
app_email = "nathan.dole@gmail.com"
app_url = "https://github.com/nathando/erpnext-opencart-api.git"
app_version = "0.0.1"

# include js, css files in header of desk.html
# app_include_css = "/assets/css/opencart_api.css"
# app_include_js = "/assets/js/opencart_site.js"

doc_events = {
    "Opencart Site": {
        "validate": "opencart_api.oc_site.oc_validate"
    },
    "Item": {
        "validate": "opencart_api.items.oc_validate",
        # "on_trash": "opencart_api.items.oc_delete"
    },
    "Item Price": {
        "validate": "opencart_api.item_prices.oc_validate",
    },
    "Customer": {
        "validate": "opencart_api.customers.oc_validate",
        "on_trash": "opencart_api.customers.oc_delete"
    },
    "Sales Order": {
        "before_save": "opencart_api.orders.before_save",
        # "before_insert": "opencart_api.orders.before_insert",
        # "after_insert": "opencart_api.orders.after_insert",
        # "validate": "opencart_api.sales_order.validate",
        # "before_submit": "opencart_api.orders.before_submit",
        # "before_cancel": "opencart_api.orders.before_cancel",
        # "before_update_after_submit": "opencart_api.orders.before_update_after_submit",
        # "on_update": "opencart_api.sales_order.on_update",
        "on_submit": "opencart_api.orders.on_submit",
        # "on_cancel": "opencart_api.orders.on_cancel",
        # "on_update_after_submit": "opencart_api.orders.on_update_after_submit",
        # "on_trash": "opencart_api.orders.on_trash"
    },
    "Sales Invoice": {
        # "on_submit": "opencart_api.sales_invoice.on_submit"
    },
    "Purchase Receipt": {
    },
    "Delivery Note": {
        # "before_submit": "opencart_api.delivery_note.before_submit",
        "on_submit": "opencart_api.delivery_note.on_submit"
    },
    "Stock Entry": {
    },
    "Comment": {
        "before_save": "opencart_api.comments.before_save",
    },
    "Communication": {
        "before_save": "opencart_api.communications.before_save",
    }
}


doctype_js = {
    "Journal Entry": ["custom_scripts/journal_entry.js"],
    "Purchase Order": ["custom_scripts/purchase_order.js"],
    "Supplier Quotation": ["custom_scripts/supplier_quotation.js"],
    "Quotation": ["custom_scripts/quotation.js"],
    "Material Request": ["custom_scripts/material_request.js"],
    "Purchase Receipt": ["custom_scripts/purchase_receipt.js"],
    "Stock Entry": ["custom_scripts/stock_entry.js"],
    "Item": ["custom_scripts/item.js"],
    "Sales Order": ["custom_scripts/sales_order.js"],
    "Sales Invoice": ["custom_scripts/sales_invoice.js"],
    "Packing Slip": ["custom_scripts/packing_slip.js"],
    "Stock Reconciliation": ["custom_scripts/stock_reconciliation.js"],
    "Warehouse": ["custom_scripts/warehouse.js"]
}

doctype_list_js = {
    "Delivery Note": ["custom_scripts/delivery_note_list.js"],
}

# Note on Fixtures (Nathan Do):
# csv fixtures files after being exported should be
# manually edited to maintain correct order as of ERPNext 4.9.2

fixtures = ["Custom Field", "Custom Script"]

scheduler_events = {
    # "all": [
    #     "opencart_api.tasks.hourly"
    # ],
    # "all": [
    #     "opencart_api.tasks.daily"
    # ],
    "hourly": [
        "opencart_api.tasks.hourly"
    ]
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/opencart_api/css/opencart_api.css"
# app_include_js = "/assets/opencart_api/js/opencart_api.js"

# include js, css files in header of web template
# web_include_css = "/assets/opencart_api/css/opencart_api.css"
# web_include_js = "/assets/opencart_api/js/opencart_site.js"
# web_include_js = "/assets/js/opencart_site.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "opencart_api.install.before_install"
# after_install = "opencart_api.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "opencart_api.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#   "Event": "frappe.core.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.core.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#   "*": {
#       "on_update": "method",
#       "on_cancel": "method",
#       "on_trash": "method"
#   }
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#   "all": [
#       "opencart_api.tasks.daily"
#   ],
#   "daily": [
#       "opencart_api.tasks.daily"
#   ],
#   "hourly": [
#       "opencart_api.tasks.hourly"
#   ],
#   "weekly": [
#       "opencart_api.tasks.weekly"
#   ]
#   "monthly": [
#       "opencart_api.tasks.monthly"
#   ]
# }

# Testing
# -------

# before_tests = "opencart_api.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
#     "runserverobj": ["opencart_api.custom_hooks.run_method.runserverobj"]
# }
