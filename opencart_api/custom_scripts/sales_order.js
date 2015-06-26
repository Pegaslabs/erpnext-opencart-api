
cur_frm.cscript.refresh = function(doc) {
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

		frappe.call({
			method: "opencart_api.oc_site.get_payment_method_code_list",
			args: {
				"site_name": doc.oc_site,
			},
			callback: function(r) {
				if(!r.exc) {
					set_field_options("oc_payment_method", [""].concat(r.message).join("\n"));
				}
			}
		});

		frappe.call({
			method: "opencart_api.oc_site.get_shipping_method_code_list",
			args: {
				"site_name": doc.oc_site,
			},
			callback: function(r) {
				if(!r.exc) {
					set_field_options("oc_shipping_method", [""].concat(r.message).join("\n"));
				}
			}
		});
	}
}




// cur_frm.cscript.refresh = function(doc, cdt, cdn) {


    // cur_frm.set_df_property("oc_status", "options", "123\n345\n678");




	// if(doc.abbr && !doc.__islocal) {
	// 	cur_frm.set_df_property("abbr", "read_only", 1);
	// }

	// if(!doc.__islocal) {
	// 	cur_frm.toggle_enable("default_currency", (cur_frm.doc.__onload &&
	// 		!cur_frm.doc.__onload.transactions_exist));
	// }

	// erpnext.company.set_chart_of_accounts_options(doc);




	// var dialog = new frappe.ui.Dialog({
	// 	title: "Replace Abbr",
	// 	fields: [
	// 		{"fieldtype": "Data", "label": "New Abbreviation", "fieldname": "new_abbr",
	// 			"reqd": 1 },
	// 		{"fieldtype": "Button", "label": "Update", "fieldname": "update"},
	// 	]
	// });

	// dialog.fields_dict.update.$input.click(function() {
	// 	args = dialog.get_values();
	// 	if(!args) return;
	// 	return frappe.call({
	// 		method: "erpnext.setup.doctype.company.company.replace_abbr",
	// 		args: {
	// 			"company": cur_frm.doc.name,
	// 			"old": cur_frm.doc.abbr,
	// 			"new": args.new_abbr
	// 		},
	// 		callback: function(r) {
	// 			if(r.exc) {
	// 				msgprint(__("There were errors."));
	// 				return;
	// 			} else {
	// 				cur_frm.set_value("abbr", args.new_abbr);
	// 			}
	// 			dialog.hide();
	// 			cur_frm.refresh();
	// 		},
	// 		btn: this
	// 	})
	// });
// 	dialog.show();
// }