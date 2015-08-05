cur_frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
	if(!doc.delivery_note) {
		frappe.throw(__("Please Delivery Note first"))
	} else {
		return {
			query: "packing_slip.update_item_details",
			filters:{ 'delivery_note': doc.delivery_note}
		}
	}
}