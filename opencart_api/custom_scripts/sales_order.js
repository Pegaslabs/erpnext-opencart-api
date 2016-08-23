cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
	if(doc.__islocal) {
		delivery_date = frappe.datetime.add_days(frappe.datetime.nowdate(), 7);
		this.frm.set_value("delivery_date", delivery_date);
	}

	if(doc.oc_site) {
		frappe.call({
			method: "opencart_api.oc_site.get_order_status_name_list",
			args: {
				"site_name": doc.oc_site,
			},
			callback: function(r) {
				if(!r.exc) {
					set_field_options("oc_status", [""].concat(r.message).join("\n"));
				}
			}
		});
	}
}
