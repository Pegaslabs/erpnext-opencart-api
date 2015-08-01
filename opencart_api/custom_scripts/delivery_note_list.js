
var old_get_indicator = frappe.get_indicator;
frappe.get_indicator = function(doc, doctype) {
	if(doc.__unsaved) {
		return [__("Not Saved"), "orange"];
	}
	if(!doctype) doctype = doc.doctype;   
    if(doctype == "Delivery Note" && doc.status == "Ready to ship") {
        return [__("Ready to ship"), "blue"]
    }
    else {
    	return old_get_indicator(doc, doctype);
    }
}
