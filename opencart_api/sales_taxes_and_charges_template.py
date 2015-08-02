import frappe


def get_first_by_territory(territory_name, company_name=None):
    all_app_territories = frappe.db.get_all("Applicable Territory", fields=['parent'], filters={'territory': territory_name, 'parenttype': 'Sales Taxes and Charges Template'})
    if all_app_territories:
        for app_territory in all_app_territories:
            template = frappe.db.get("Sales Taxes and Charges Template", app_territory.get('parent'))
            if company_name:
                if company_name == template.get('company'):
                    return template.get('name')
            else:
                return template.get('name')
    else:
        if frappe.db.get_value('Territory', territory_name, 'parent_territory') == 'Rest Of The World':
            all_app_territories = frappe.db.get_all("Applicable Territory", fields=['parent'], filters={'territory': 'Rest Of The World', 'parenttype': 'Sales Taxes and Charges Template'})
            for app_territory in all_app_territories:
                template = frappe.db.get("Sales Taxes and Charges Template", app_territory.get('parent'))
                if company_name:
                    if company_name == template.get('company'):
                        return template.get('name')
                else:
                    return template.get('name')
