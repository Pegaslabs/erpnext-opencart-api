cur_frm.cscript.is_pos = function (doc, dt, dn, callback_fn) {
	cur_frm.cscript.hide_fields(this.frm.doc);
	if(cint(this.frm.doc.is_pos)) {
		if(!this.frm.doc.company) {
			this.frm.set_value("is_pos", 0);
			msgprint(__("Please specify Company to proceed"));
		} else {
			var me = this;
			return this.frm.call({
				doc: me.frm.doc,
				method: "set_missing_values",
				callback: function(r) {
					if(!r.exc) {
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
