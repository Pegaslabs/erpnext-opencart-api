cur_frm.add_fetch('company','default_letter_head','letter_head');
cur_frm.add_fetch('company','default_print_heading','select_print_heading');

cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
	if(!doc.__islocal) {
		cur_frm.cscript.setup_dashboard(doc);
	}
}

cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);
	if (doc.sales_order) {
		frappe.call({
			type: "GET",
			method: "opencart_api.sales_invoice.get_sales_statistic",
			args: {
				sales_order: doc.sales_order
			},
			callback: function(r) {
				if (doc.sales_order) {
					cur_frm.dashboard.add_doctype_badge("Sales Order", doc.sales_order);
				}
				if (Object.keys(r.message.delivery_note).length >= 1) {
					cur_frm.dashboard.add_doctype_badge("Delivery Note",  r.message.delivery_note, "sales_order");
				}
				if (Object.keys(r.message.packing_slip).length >= 1) {
					cur_frm.dashboard.add_doctype_badge("Packing Slip", r.message.packing_slip, "sales_order");
				}
			}
		});
	}
}

cur_frm.dashboard.add_doctype_badge = function(doctype, no, fieldname) {
	if(frappe.model.can_read(doctype)) {
		this.add_badge(__(doctype), no, doctype, function() {
			frappe.route_options = {};
			if (fieldname) {
				frappe.route_options[fieldname] = cur_frm.doc.sales_order;
			}
			if ((no != cur_frm.doc.sales_order) && (no.length > 1)) {
				frappe.set_route("List", doctype);
			} else {
			 	frappe.set_route("Form", doctype, no);
			}
		}).attr("data-doctype", doctype);
		}
	}

cur_frm.dashboard.add_badge = function(label, no, doctype, onclick) {
		if (no != cur_frm.doc.sales_order) {
			for (var i in no) {
				var label = label + '<br>' + no[i];
			}
		} else {
			var label = label + '<br>' + no;
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