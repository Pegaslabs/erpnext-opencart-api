
cur_frm.cscript['Make Packing Slip'] = function() {
	frappe.model.open_mapped_doc({
		method: "opencart_api.delivery_note.make_packing_slip",
		frm: cur_frm
	})
}
