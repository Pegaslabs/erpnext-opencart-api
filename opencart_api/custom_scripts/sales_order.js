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

cur_frm.cscript.customer = function() {
    var me = this;
	erpnext.utils.get_party_details(this.frm, null, null, function(){me.apply_pricing_rule()});
    
    // custom code
    // updating Sales Order company
    frappe.model.with_doc("Customer", me.frm.doc.customer, function(r) {
	    var doc_customer = frappe.model.get_doc("Customer", me.frm.doc.customer);
        if(doc_customer.oc_site && doc_customer.oc_customer_id) {
            frappe.model.with_doc("Opencart Site", doc_customer.oc_site, function(r) {
                var doc_oc_site = frappe.model.get_doc("Opencart Site", doc_customer.oc_site);
                me.frm.set_value("company", doc_oc_site.company);
            });
        }
	});

	// updating taxes and shipping rule
}


// cur_frm.cscript.validate = function(doc) {
	
// }

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