cur_frm.add_fetch('delivery_note','letter_head','letter_head');
// cur_frm.add_fetch('delivery_note','select_print_heading','select_print_heading');

cur_frm.cscript.on_submit = function(doc, сdt, сdn) {
    frappe.set_route("Form", "Delivery Note", doc.delivery_note);
}

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

frappe.scan_prompt_dialog1 = function(callback, notification) {
    if (notification) {
        var label = "";
        if (notification[0] == "danger") {
            label = "<h4><span class=\"label label-danger\">" + notification[1] + "</span></h4>";
        } else if (notification[0] == "success") {
            label = "<h4><span class=\"label label-success\">" + notification[1] + "</span></h4>";
        } else {
            label = "<h4><span class=\"label label-info\">" + notification[1] + "</span></h4>";
        }

        var fields = [
            {
                fieldname:"msg",
                fieldtype:"HTML",
                options: "<div style=\"margin: 0px\" class=\"form-group\">" +
                            label +
                        "</div>"
            },
            {fieldtype:"Section Break"},
            {label:"Barcode", fieldtype:"Data", reqd: 1}
        ];
    } else {
        var fields = [
            {label:"Barcode", fieldtype:"Data", reqd: 1}
        ];
    }
    var d = new frappe.ui.Dialog({
        fields: fields,
        title: __("Scan Items"),
    })
    d.set_primary_action(__("Proceed"), function() {
        var values = d.get_values();
        if(!values) {
            return;
        }
        d.hide();
        callback(values);
    })

    d.$wrapper.on("shown.bs.modal", function() {
        d.$wrapper.find(".modal-body :input:first").get(0).focus();
    })
    d.show();
}

frappe.scan_prompt_dialog2 = function(barcode, item, callback) {
    var fields = [
        {
            fieldname:"item_description",
            fieldtype:"HTML",
            options: "<div style=\"margin: 0px\" class=\"form-group\">" +
                        "<label style=\"padding-right: 0px;\" class=\"control-label\">Item Code</label>" +
                        "<div class=\"control-input-wrapper\">" +
                            "<div style=\"\" class=\"control-value like-disabled-input\">" + item.item_code + "</div>" +
                        "</div>" +
                    "</div>" +
                    "<div style=\"margin: 0px\" class=\"form-group\">" +
                        "<label style=\"padding-right: 0px;\" class=\"control-label\">Item Name</label>" +
                        "<div class=\"control-input-wrapper\">" +
                            "<div style=\"\" class=\"control-value like-disabled-input\">" + item.item_name + "</div>" +
                        "</div>" +
                    "</div>"
        },
        {fieldtype:"Column Break"},
        {
            fieldname:"image",
            fieldtype:"HTML",
            options: "<img src='" + item.image + "' class='img-responsive'>"
        },
        {fieldtype:"Section Break"},
        {
            fieldname:"barcode",
            fieldtype:"HTML",
            options: "<div style=\"margin: 0px\" class=\"form-group\">" +
                        "<label style=\"padding-right: 0px;\" class=\"control-label\">Barcode</label>" +
                        "<div class=\"control-input-wrapper\">" +
                            "<div style=\"\" class=\"control-value like-disabled-input\">" + barcode + "</div>" +
                        "</div>" +
                    "</div>"
        },
        {fieldtype:"Column Break"},
        {
            label:"Quantity",
            fieldname: "qty",
            fieldtype:"Float",
            reqd: 1,
            default: 1
        }
    ];
    var d = new frappe.ui.Dialog({
        fields: fields,
        title: __("Scan Items"),
    })
    d.set_primary_action(__("Proceed"), function() {
        var values = d.get_values();
        if(!values) {
            return;
        }
        d.hide();
        // patch values from dialog
        values.barcode = barcode;
        callback(values);
    })

    d.$wrapper.on("shown.bs.modal", function() {
        d.$wrapper.find(".modal-body :input:last").get(0).focus();
    })
    d.show();
}

frappe.scan_prompt = function(barcode, item, callback, notification) {
    // initial dialog to enter barcode and quantity
    if (barcode == undefined && item == undefined) {
        frappe.scan_prompt_dialog1(callback, notification);
        return;
    }
    if (barcode) {
        if (item) {
            frappe.scan_prompt_dialog2(barcode, item, callback);
        } else {
            frappe.scan_prompt_dialog1(callback, notification);
        }
    } else {
        frappe.scan_prompt_dialog1(callback, notification);
    }
}

// ---
//             var d = new frappe.ui.Dialog({
//                 title: __("Upload User Permissions"),
//                 fields: [
//                     {
//                         fieldtype:"HTML",
//                         options: '<p class="text-muted"><ol>'+
//                             "<li>"+__("Upload CSV file containing all user permissions in the same format as Download.")+"</li>"+
//                             "<li><strong>"+__("Any existing permission will be deleted / overwritten.")+"</strong></li>"+
//                         '</p>'
//                     },
//                     {
//                         fieldtype:"Attach", fieldname:"attach",
//                     }
//                 ],
//                 primary_action_label: __("Upload and Sync"),
//                 primary_action: function() {
//                     frappe.call({
//                         method:"frappe.core.page.user_permissions.user_permissions.import_user_permissions",
//                         args: {
//                             filedata: d.fields_dict.attach.get_value()
//                         },
//                         callback: function(r) {
//                             if(!r.exc) {
//                                 msgprint(__("Permissions Updated"));
//                                 d.hide();
//                             }
//                         }
//                     });
//                 }
//             });
//             d.show();


// --------------
// var d = new frappe.ui.Dialog({
//                 title: "Workflow: "
//                     + frappe.workflow.workflows[me.frm.doctype].name
//             })
//             var next_html = $.map(frappe.workflow.get_transitions(me.frm.doctype, state),
//                 function(d) {
//                     return d.action.bold() + __(" by Role ") + d.allowed;
//                 }).join(", ") || __("None: End of Workflow").bold();

//             $(d.body).html("<p>"+__("Current status")+": " + state.bold() + "</p>"
//                 + "<p>"+__("Document is only editable by users of role")+": "
//                     + frappe.workflow.get_document_state(me.frm.doctype,
//                         state).allow_edit.bold() + "</p>"
//                 + "<p>"+__("Next actions")+": "+ next_html +"</p>"
//                 + (me.frm.doc.__islocal ? ("<div class='alert alert-info'>"
//                     +__("Workflow will start after saving.")+"</div>") : "")
//                 + "<p class='help'>"+__("Note: Other permission rules may also apply")+"</p>"
//                 ).css({padding: '15px'});
//             d.show();
// ==================


function scan_items(frm, cdt, cdn, barcode, item, callback, notification) {
    if (frm.doc.items) {
        check_scanned_items(frm);
        if (callback == undefined) {
            callback = function(data1) {
                frappe.call({
                    method:"opencart_api.packing_slip.get_item_by_barcode",
                    args: {
                        barcode: data1.barcode
                    },
                    callback: function(r) {
                        if(!r.exc) {
                            if(r.message) {
                                var item = r.message;
                                scan_items(frm, cdt, cdn, data1.barcode, item, function(data2) {
                                    var items = frm.doc.items || [];
                                    var item_found = false;
                                    for(var i = 0; i < items.length; i++) {
                                        if (items[i].item_code == item.item_code) {
                                            item_found = true;
                                            if (!items[i].scanned_qty) {
                                                items[i].scanned_qty = 0;
                                            }
                                            if (items[i].scanned_qty + data2.qty > items[i].qty) {
                                                var exceed_qty = items[i].scanned_qty + data2.qty - items[i].qty;
                                                scan_items(frm, cdt, cdn, data1.barcode, undefined, undefined, ["danger", "Not added: total quantity of scanned items will exceed the required quantity more then " + exceed_qty + " items"]);
                                                break;
                                            }
                                            items[i].scanned_qty += data2.qty;
                                            items[i].barcode = data2.barcode;
                                            frm.save("Save", function() {
                                                scan_items(frm, cdt, cdn, data1.barcode, undefined, undefined, ["success", "Last successful scanning: " + data2.qty + " " + item.item_code + " items"]);
                                            });
                                            break;
                                        }
                                    }
                                    if (!item_found) {
                                        scan_items(frm, cdt, cdn, data1.barcode, undefined, undefined, ["danger", "Not added: Item \"" + item.item_code + "\" not found in the Item list of this Packing Slip"]);
                                    }
                                });
                            } else {
                                scan_items(frm, cdt, cdn, data1.barcode, undefined, undefined, ["danger", "Item with barcode \"" + data1.barcode + "\" not found"]);
                            }
                        }
                    }
                });
            }
        }
        frappe.scan_prompt(barcode, item, callback, notification);
    } else {
        frappe.msgprint('You cannot scan items for empty item list.');
    }
}

frappe.ui.form.on("Packing Slip", "scan_items", scan_items);

function check_scanned_items(frm) {
    // alert("background-color:red");
    // var d = locals[cdt][cdn];
    var wrapper = $(cur_frm.fields_dict.items.wrapper);
    var items = frm.doc.items || [];
    for(var i = 0; i < items.length; i++){
        // items[i].scanned_qty = 0.0;
        var row_wrapper = wrapper.find("[data-idx='"+ items[i].idx +"']").data("grid_row").wrapper;
        if(row_wrapper) {
            if (!items[i].scanned_qty || items[i].scanned_qty == 0) {
                // red
                row_wrapper.css('background-color', '#ff5858');
            } else if(items[i].scanned_qty && items[i].scanned_qty < items[i].qty) {
                // orange
                row_wrapper.css('background-color', '#ffa00a');
            } else if(items[i].scanned_qty && items[i].scanned_qty == items[i].qty) {
                // green
                row_wrapper.css('background-color', '#98d85b');
            }
        }
    }
}

frappe.ui.form.on("Packing Slip", "check_scanned_items", function(frm) {
    check_scanned_items(frm);
});

cur_frm.cscript.reset_scanned_items = function(doc) {
    // alert("background-color:red");
    // var d = locals[cdt][cdn];
    var items = doc.items || [];
    for(var i = 0; i < items.length; i++){
        items[i].scanned_qty = 0.0;
    }
    refresh_field('items');
}
