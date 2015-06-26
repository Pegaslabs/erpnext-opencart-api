import frappe


def get_first_by_territory(territory_name, company_name=None):
    filters = None
    if company_name:
        filters = {"company": company_name}
    for template in frappe.db.get_all("Sales Taxes and Charges Template", filters=filters):
        doc_template = frappe.get_doc("Sales Taxes and Charges Template", template.name)
        for doc_territory in doc_template.territories:
            if territory_name == doc_territory.get("territory"):
                return doc_template
