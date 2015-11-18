cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
	if(doc.__islocal) {
		delivery_date = frappe.datetime.add_days(frappe.datetime.nowdate(), 7);
		this.frm.set_value("delivery_date", delivery_date);
	} else {
		cur_frm.cscript.setup_dashboard(doc);
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

cur_frm.cscript.oc_is_shipping_included_in_total = function() {
	var me = this;
    me.shipping_rule();
}

cur_frm.cscript.make_sales_invoice = function() {
	frappe.model.open_mapped_doc({
		method: "opencart_api.sales_order.make_sales_invoice",
		frm: cur_frm
	})
}

cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);

	frappe.call({
		type: "GET",
		method: "opencart_api.sales_invoice.get_sales_statistic",
		args: {
			sales_order: doc.name
		},
		callback: function(r) {
			if (Object.keys(r.message.back_order).length > 0) {
				cur_frm.dashboard.add_doctype_badge("Back Order", "customer", r.message.back_order, "customer");
			}
			if (Object.keys(r.message.sales_invoice).length > 0) {
				cur_frm.dashboard.add_doctype_badge("Sales Invoice", "sales_order", r.message.sales_invoice);
			}
			if (Object.keys(r.message.delivery_note).length > 0) {
				cur_frm.dashboard.add_doctype_badge("Delivery Note", "sales_order", r.message.delivery_note);
			}
			if (Object.keys(r.message.packing_slip).length > 0) {
				cur_frm.dashboard.add_doctype_badge("Packing Slip", "sales_order", r.message.packing_slip);
			}
		}
	});
}

cur_frm.dashboard.add_doctype_badge = function(doctype, fieldname, no, filter_fieldname) {
	if(frappe.model.can_read(doctype)) {
		this.add_badge(__(doctype), no, doctype, function() {
			frappe.route_options = {};
			if (!filter_fieldname) {
				filter_fieldname = "name"
			}
			frappe.route_options[fieldname] = cur_frm.doc[filter_fieldname];
			if (no.length > 1) {
					frappe.set_route("List", doctype);
			} else {
			 	frappe.set_route("Form", doctype, no);
			}
		}).attr("data-doctype", doctype);
	}
}

cur_frm.dashboard.add_badge = function(label, no, doctype, onclick) {
		for (var i in no) {
			var label = label + '<br>' + no[i];
		}
		var badge = $(repl('<div class="col-md-3">\
			<div class="alert-badge">\
				<a class="badge-link grey">%(label)s</a>\
			</div></div>', {label:label, icon: frappe.boot.doctype_icons[doctype]}))
				.appendTo(this.body)

		badge.find(".badge-link").click(onclick);
		this.wrapper.toggle(true);

		return badge.find(".alert-badge");
}
