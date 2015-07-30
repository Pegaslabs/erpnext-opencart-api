
cur_frm.cscript['Make Delivery Note'] = function() {
	frappe.model.open_mapped_doc({
		method: "opencart_api.sales_invoice.make_delivery_note",
		frm: cur_frm
	})
}