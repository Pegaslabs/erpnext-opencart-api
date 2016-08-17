app_name = "opencart_api"
app_title = "Opencart API"
app_publisher = "olhonko"
app_description = "App for connecting Opencart through APIs."
app_icon = "icon-book"
app_color = "#589494"
app_email = "olhonko@gmail.com"
app_url = "https://github.com/olhonko/erpnext-opencart-api.git"
app_version = "0.0.1"

# include js, css files in header of desk.html
# app_include_css = "/assets/css/opencart_api.css"
# app_include_js = "/assets/js/opencart_site.js"

doc_events = {
    "Bin": {
        "validate": "opencart_api.items.on_bin_update"
    },
    "Opencart Site": {
        "validate": "opencart_api.oc_site.oc_validate"
    },
    "Item": {
        "validate": "opencart_api.items.oc_validate"
    },
    "Item Price": {
        "on_update": "opencart_api.item_prices.oc_on_update",
    },
    "Customer": {
        "validate": "opencart_api.customers.oc_validate",
        "on_trash": "opencart_api.customers.oc_delete"
    },
    "Sales Order": {
        "before_save": "opencart_api.orders.before_save",
        # "before_insert": "opencart_api.orders.before_insert",
        # "after_insert": "opencart_api.orders.after_insert",
        "validate": "opencart_api.orders.validate",
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
    "Communication": {
        "before_save": "opencart_api.communications.before_save",
    }
}

doctype_js = {
    "Item": ["custom_scripts/item.js"],
    "Sales Order": ["custom_scripts/sales_order.js"],
    "Stock Reconciliation": ["custom_scripts/stock_reconciliation.js"],
    "Warehouse": ["custom_scripts/warehouse.js"]
}

doctype_list_js = {
}

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
