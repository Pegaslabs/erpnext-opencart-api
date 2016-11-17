from frappe import _


def get_data():
    return [
        {
            "module_name": "Opencart API",
            "label": _("Opencart API"),
            "color": "#00004d",
            "icon": "octicon octicon-git-compare",
            "idx": 53,
            "reverse": 0,
            "type": "module"
        },
        {
            "module_name": "Opencart Site",
            "_doctype": "Opencart Site",
            "color": "#00004d",
            "icon": "octicon octicon-gist",
            "idx": 53,
            "reverse": 0,
            "type": "link",
            "link": "List/Opencart Site"
        }
    ]
