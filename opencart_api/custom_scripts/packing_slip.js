cur_frm.cscript.validate_duplicate_items = function(doc, ps_detail) {
    for(var i=0; i<ps_detail.length; i++) {
        for(var j=0; j<ps_detail.length; j++) {
            if(i!=j && ps_detail[i].item_code && ps_detail[i].item_code==ps_detail[j].item_code) {
                msgprint(__("You have entered duplicate items. Please rectify and try again."));
                validated = false;
                return;
            }
        }
    }
}

cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
    if(!doc.__islocal && doc.docstatus == 0) {
        cur_frm.cscript.setup_dashboard(doc);
    }
}

cur_frm.cscript.setup_dashboard = function(doc) {
    cur_frm.dashboard.reset(doc);
    cur_frm.dashboard.add_doctype_badge("Delivery Note", doc.delivery_note);
}

cur_frm.dashboard.add_doctype_badge = function(doctype, no) {
    if(frappe.model.can_read(doctype)) {
        this.add_badge(__(doctype), no, doctype, function() {
            frappe.set_route("Form", doctype, no);
        }).attr("data-doctype", doctype);
    }
}

cur_frm.dashboard.add_badge = function(label, no, doctype, onclick) {
        var label = label + '<br>' + no;

        var badge = $(repl('<div class="col-md-3">\
            <div class="alert-badge">\
                <a class="badge-link grey">%(label)s</a>\
            </div></div>', {label:label, icon: frappe.boot.doctype_icons[doctype]}))
                .appendTo(this.body)

        badge.find(".badge-link").click(onclick);
        this.wrapper.toggle(true);

        return badge.find(".alert-badge");
}
