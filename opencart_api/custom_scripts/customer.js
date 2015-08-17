cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);
	if(doc.__islocal)
		return;
	if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager"))
		cur_frm.dashboard.set_headline('<span class="text-muted">'+ __('Loading...')+ '</span>')

	cur_frm.dashboard.add_doctype_badge("Opportunity", "customer");
	cur_frm.dashboard.add_doctype_badge("Quotation", "customer");
	cur_frm.dashboard.add_doctype_badge("Sales Order", "customer");
	cur_frm.dashboard.add_doctype_badge("Delivery Note", "customer");
	cur_frm.dashboard.add_doctype_badge("Sales Invoice", "customer");
	cur_frm.dashboard.add_doctype_badge("Back Order", "customer");

	return frappe.call({
		type: "GET",
		method: "opencart_api.patched.erpnext.selling.doctype.customer.customer.get_dashboard_info",
		args: {
			customer: cur_frm.doc.name
		},
		callback: function(r) {
			if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager")) {
				if(r.message["company_currency"].length == 1) {
					cur_frm.dashboard.set_headline(
						__("Total Billing This Year: ") + "<b>"
						+ format_currency(r.message.billing_this_year, r.message["company_currency"][0])
						+ '</b> / <span class="text-muted">' + __("Unpaid") + ": <b>"
						+ format_currency(r.message.total_unpaid, r.message["company_currency"][0])
						+ '</b></span>');
				}
			}
			cur_frm.dashboard.set_badge_count(r.message);
		}
	});
}
