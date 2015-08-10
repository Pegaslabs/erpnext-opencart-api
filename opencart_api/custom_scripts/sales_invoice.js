cur_frm.add_fetch('company','default_letter_head','letter_head');
cur_frm.add_fetch('company','default_print_heading','select_print_heading');

cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
	if(!doc.__islocal) {
		cur_frm.cscript.setup_dashboard(doc);
	}
}

cur_frm.cscript['Make Delivery Note'] = function() {
	frappe.model.open_mapped_doc({
		method: "opencart_api.sales_invoice.make_delivery_note",
		frm: cur_frm
	})
}

cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);

	frappe.call({
		type: "GET",
		method: "opencart_api.sales_invoice.get_sales_statistic",
		args: {
			customer: doc.customer
		},
		callback: function(r) {
			if (Object.keys(r.message.sales_order).length >= 1) {
				cur_frm.dashboard.add_doctype_badge("Sales Order", "customer", r.message.sales_order);
			}
			if (Object.keys(r.message.delivery_note).length >= 1) {
				cur_frm.dashboard.add_doctype_badge("Delivery Note", "customer", r.message.delivery_note);
			}
			if (r.message.packing_slip) {
				for (var i in r.message.packing_slip.delivery_note) {
					if (r.message.packing_slip.packing_slip[i]) {
						cur_frm.dashboard.add_doctype_badge("Packing Slip", "delivery_note", r.message.packing_slip.packing_slip[i], r.message.packing_slip.delivery_note[i][0]);
					}
				}
			}
		}
	});
}

cur_frm.dashboard.add_doctype_badge = function(doctype, fieldname, no, del_no) {
	if(frappe.model.can_read(doctype)) {
		this.add_badge(__(doctype), no, doctype, function() {
			frappe.route_options = {};
			if (fieldname != "delivery_note") {
				frappe.route_options[fieldname] = cur_frm.doc.customer;
			} else {
				frappe.route_options[fieldname] = del_no;
			}
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
		var badge = $(repl('<div class="col-md-4">\
			<div class="alert-badge">\
				<a class="badge-link grey">%(label)s</a>\
			</div></div>', {label:label, icon: frappe.boot.doctype_icons[doctype]}))
				.appendTo(this.body)

		badge.find(".badge-link").click(onclick);
		this.wrapper.toggle(true);

		return badge.find(".alert-badge");
	}