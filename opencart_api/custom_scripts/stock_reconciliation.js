frappe.ui.form.on("Stock Reconciliation", "get_items", function(frm) {
	frappe.prompt({label:"Warehouse", fieldtype:"Link", options:"Warehouse", reqd: 1},
		function(data) {
			frappe.call({
				method:"opencart_api.stock_reconciliation.get_items",
				args: {
					warehouse: data.warehouse,
					posting_date: frm.doc.posting_date,
					posting_time: frm.doc.posting_time
				},
				callback: function(r) {
					var items = [];
					frm.clear_table("items");
					for(var i=0; i< r.message.length; i++) {
						var d = frm.add_child("items");
						$.extend(d, r.message[i]);
					}
					frm.refresh_field("items");
				}
			});
		}
	, __("Get Items"), __("Update"));
});