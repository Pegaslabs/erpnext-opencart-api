cur_frm.cscript.is_pos = function (doc, dt, dn, callback_fn) {
	var me = this;
	var initial_price_list = me.frm.doc.selling_price_list;
	var initial_price_list_currency = me.frm.doc.price_list_currency;
	var initial_plc_conversion_rate = me.frm.doc.plc_conversion_rate;
	var initial_currency = me.frm.doc.currency;
	var initial_conversion_rate = me.frm.doc.conversion_rate;
	cur_frm.cscript.hide_fields(this.frm.doc);
	if(cint(this.frm.doc.is_pos)) {
		if(!this.frm.doc.company) {
			this.frm.set_value("is_pos", 0);
			msgprint(__("Please specify Company to proceed"));
		} else {
			return this.frm.call({
				doc: me.frm.doc,
				method: "opencart_api.sales_invoice.set_missing_values",
				callback: function(r) {
					if(!r.exc) {
						if (me.frm.doc.selling_price_list != initial_price_list) {
							me.frm.doc.selling_price_list = initial_price_list;
							me.frm.doc.price_list_currency = initial_price_list_currency;
							me.frm.doc.plc_conversion_rate = initial_plc_conversion_rate;
							me.frm.doc.currency = initial_currency;
							me.frm.doc.conversion_rate = initial_conversion_rate;
						}
						me.frm.script_manager.trigger("update_stock");
						frappe.model.set_default_values(me.frm.doc);
						me.set_dynamic_labels();
						me.calculate_taxes_and_totals();
						if(callback_fn) callback_fn();
					}
				}
			});
		}
	}
}
