cur_frm.add_fetch('delivery_note','letter_head','letter_head');
// cur_frm.add_fetch('delivery_note','select_print_heading','select_print_heading');

cur_frm.cscript.on_submit = function(doc, сdt, сdn) {
    frappe.set_route("Form", "Delivery Note", doc.delivery_note);
}

function print_scan_items_log() {
    var $table = $('<table class="table table-hover" style="border: 1px solid #D1D8DD;"></table>');
    var $th = $('<tr style="background-color: #F7FAFC; font-size: 85%; color: #8D99A6"></tr>');
    var $tbody = $('<tbody id="scan-items-tbody" style="font-family: Helvetica Neue, Helvetica, Arial, "Open Sans", sans-serif;font-size: 11.9px; line-height: 17px; color: #8D99A6;  background-color: #fff;"></tbody>');
    $th.html('<th>Item Code</th><th>Barcode</th><th>Quantity</th><th>Status</th>');

    for(var i=0; i < cur_frm.cscript.scanned_items.length; i++) {
        $tr = $('<tr>');
        $tr.append('<td>' + cur_frm.cscript.scanned_items[i].item_code + '</td>');
        $tr.append('<td>' + cur_frm.cscript.scanned_items[i].barcode + '</td>');
        $tr.append('<td>' + cur_frm.cscript.scanned_items[i].quantity + '</td>');
        $tr.append('<td>' + cur_frm.cscript.scanned_items[i].status + '</td>');
        $tbody.append($tr);
    }

    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');

    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['scan_items_log'].wrapper).html(msg);
}


frappe.scan_prompt = function(fields, callback, title, primary_label) {
    if(!$.isArray(fields)) fields = [fields];
    var d = new frappe.ui.Dialog({
        fields: fields,
        title: title || __("Enter Value"),
    })
    d.set_primary_action(primary_label || __("Submit"), function() {
        var values = d.get_values();
        if(!values) {
            return;
        }
        d.hide();
        callback(values);
    })

    d.get_input("barcode").on("keypress", function(e) {
            if(e.which===13) {
                d.get_primary_btn().trigger("click");
            }
    });
    d.$wrapper.on("shown.bs.modal", function() {
        d.$wrapper.find(".modal-body :input:first").get(0).focus();
    })
    d.show();
    return d;
}


cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
    if(!doc.__islocal && doc.docstatus == 0) {
        cur_frm.cscript.setup_dashboard(doc);
    }
    cur_frm.cscript.scanned_items = [];
    cur_frm.cscript.items_to_scan = {};

    for(var i=0; i < doc.items.length; i++) {
        cur_frm.cscript.items_to_scan[doc.items[i].item_code] = {
            "item_code": doc.items[i].item_code,
            "quantity": doc.items[i].qty,
            "scanned_quantity": 0,
            "barcode": ""
        };
    }
}


function on_item_scanned(item, scanned_quantity) {
    if(cur_frm.cscript.items_to_scan[item.item_code]) {
        var item_counting = cur_frm.cscript.items_to_scan[item.item_code]
        
        if(item_counting.scanned_quantity + scanned_quantity > item_counting.quantity) {
            frappe.msgprint("Warning. It is already scanned " + item_counting.scanned_quantity + " of " + item_counting.quantity + " items (Item Code: " + item.item_code + ", Barcode: " + item.barcode + ").");
        } else {
            item_counting.scanned_quantity += 1;
            item_counting["barcode"] = item.barcode;
            cur_frm.cscript.scanned_items.push({
                "item_code": item.item_code,
                "barcode": item.barcode,
                "quantity": scanned_quantity,
                "status": 'Scanned'
            });
            print_scan_items_log();
        }
    }
    else {
        frappe.msgprint("Warning. Item not found it the item list (Item Code: " + item.item_code + ", Barcode: " + item.barcode + ").");
    }
}


function scan_items(frm) {
    print_scan_items_log();
    frappe.scan_prompt([{label:"Barcode", fieldtype:"Data", reqd: 1},
                        {fieldtype:"Column Break"},
                        {label:"Quantity", fieldtype:"Float", reqd: 1, default: 1}
                       ],
        function(data) {
            frappe.call({
                method:"opencart_api.packing_slip.get_item_by_barcode",
                args: {
                    barcode: data.barcode
                },
                callback: function(r) {
                    if(!r.exc) {
                        if(r.message) {
                            on_item_scanned(r.message, data.quantity);
                        } else {
                            frappe.msgprint("Could not found Item with barcode " + data.barcode)
                        }
                    }
                    scan_items(frm);
                }
            });
        }
    , __("Scan Items"), __("Proceed"));
}

frappe.ui.form.on("Packing Slip", "scan_items", scan_items);


frappe.ui.form.on("Packing Slip", "check_scanned_items", function(frm) {
    var is_all_ok = true;
    for (var key in cur_frm.cscript.items_to_scan) {
        var item_counting = cur_frm.cscript.items_to_scan[key];
        if(item_counting.scanned_quantity == 0) {
            is_all_ok = false;
            frappe.msgprint("None of " + item_counting.quantity + " items were scanned (Item Code: " + item_counting.item_code + ", Barcode: " + item_counting.barcode + ").");
        } else if(item_counting.scanned_quantity < item_counting.quantity) {
            is_all_ok = false;
            frappe.msgprint("Only " + item_counting.scanned_quantity + " of " + item_counting.quantity + " items were scanned (Item Code: " + item_counting.item_code + ", Barcode: " + item_counting.barcode + ").");
        } else if(item_counting.scanned_quantity > item_counting.quantity) {
            is_all_ok = false;
            frappe.msgprint("Error. Scanned items count " + item_counting.scanned_quantity + " exceeds the required item count " + item_counting.quantity + ".");
        }

    }
    if(is_all_ok) {
        frappe.msgprint("All scanned items are matched.");
    }
});

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