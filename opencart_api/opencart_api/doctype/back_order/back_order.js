// cur_frm.cscript.refresh = function(doc, dt, dn) {
// 	this._super();
// 	this.frm.dashboard.reset();

// 	if (this.frm.doc.docstatus===0) {
// 		cur_frm.add_custom_button(__('From Delivery Note'),
// 			function() {
// 				frappe.model.map_current_doc({
// 					method: "opencart_api.delivery.make_back_order",
// 					source_doctype: "Delivery Note",
// 					get_query_filters: {
// 						docstatus: 1,
// 						status: ["!=", "Lost"],
// 						order_type: cur_frm.doc.order_type,
// 						customer: cur_frm.doc.customer || undefined,
// 						company: cur_frm.doc.company
// 					}
// 				})
// 			});
// 	}

// 	this.order_type(doc);
// }

// cur_frm.cscript.order_type = function() {
// 	this.frm.toggle_reqd("delivery_date", this.frm.doc.order_type == "Sales");
// }

// cur_frm.cscript.tc_name = function() {
// 	this.get_terms();
// }

// cur_frm.cscript.warehouse = function(doc, cdt, cdn) {
// 	var item = frappe.get_doc(cdt, cdn);
// 	if(item.item_code && item.warehouse) {
// 		return this.frm.call({
// 			method: "erpnext.stock.get_item_details.get_available_qty",
// 			child: item,
// 			args: {
// 				item_code: item.item_code,
// 				warehouse: item.warehouse,
// 			},
// 		});
// 	}
// }

// cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
// 	if(cint(frappe.boot.notification_settings.sales_order)) {
// 		cur_frm.email_doc(frappe.boot.notification_settings.sales_order_message);
// 	}
// }
