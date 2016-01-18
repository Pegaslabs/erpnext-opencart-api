
cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
    if(!doc.__islocal) {
        frappe.call({
            method:"opencart_api.bins.get_warehouses",
            args: {
                "item_code": doc.item_code,
            },
            callback: function(r) {
                if(!r.exc && r.message) {
                    print_warehouses(r.message);
                }
            }
        });
        this.frm.add_custom_button(__('Sync from Opencart'), this.sync_item_from_opencart).addClass("btn-primary");
    }

    set_autocomplete_field("Opencart Product", "category");
    set_autocomplete_field("Opencart Product", "manufacturer");
    set_autocomplete_field("Opencart Product", "stock_status");
    set_autocomplete_field("Opencart Product", "tax_class");
}

frappe.ui.form.on("Item", "onload", function(frm) {
    cur_frm.category_names = {};
    frappe.call({
        method: "opencart_api.oc_site.get_category_names",
        callback: function(r) {
            if(!r.exc && r.message) {
                cur_frm.category_names = r.message;
            }
        }
    });
});

print_warehouses = function(message, update) {
    var $table = $('<table class="table table-hover" style="border: 1px solid #D1D8DD;"></table>');
    var $th = $('<tr style="background-color: #F7FAFC; font-size: 85%; color: #8D99A6"></tr>');
    var $tbody = $('<tbody style="font-family: Helvetica Neue, Helvetica, Arial, "Open Sans", sans-serif;font-size: 11.9px; line-height: 17px; color: #8D99A6;  background-color: #fff;"></tbody>');
    $th.html('<th>Warehouse</th><th>Actual Quantity</th><th>Stock Value</th>');
    var groups = $.map(message, function(o){
        $tr = $('<tr>');
        $tr.append('<td>' + o[0] + '</td>');
        $tr.append('<td>' + o[1] + '</td>');
        if (o[1]> 0) {
            $tr.append('<td>' + o[2] + '</td>');
        }
        $tbody.append($tr);
    })
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');  
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['warehouses'].wrapper).html(msg);
}

cur_frm.cscript.sync_item_from_opencart = function(label, status){
    var doc = cur_frm.doc;
    frappe.call({
        freeze: true,
        freeze_message: __("Syncing"),
        method: "opencart_api.items.sync_item_from_oc",
        args: {item_code: doc.item_code},
        callback: function(r){
            cur_frm.reload_doc();
        }
    });
}

filter_categories  = function(string, array) {
    var result_list = [];
    $.each(array, function(i, element) {
        if(element.toUpperCase().indexOf(string.toUpperCase()) != -1) {
            result_list.push(element);
        }
    });
    return result_list
}

set_autocomplete_field = function(doctype, field_name) {
    var oc_field_name = "oc_" + field_name + "_name";
    var oc_field_id = "oc_" + field_name + "_id";
    var get_names_method = "opencart_api.items.get_" + field_name + "_names";
    var get_id_method = "opencart_api.items.get_" + field_name + "_id";
    var df = frappe.meta.get_docfield(doctype, oc_field_name, cur_frm.docname);
    df.on_make = function(field) {
        $(field.input_area).addClass("ui-front");
        field.$input.autocomplete({
            minLength: 0,
            source: function(request, response) {
                var open_form = frappe.ui.form.get_open_grid_form();
                var id = open_form.fields_dict[oc_field_id];
                var category_names = cur_frm.category_names[open_form.fields_dict.oc_site.value];
                if(request) {
                    id.set_value("");
                    id.refresh();
                }
                if(field_name == "category") {
                    if(category_names) {
                        if(request.term) {
                            response(filter_categories(request.term, category_names));
                        } else {
                            response(category_names);
                        }
                    } else {
                        response(false);
                    }
                } else {
                    frappe.call({
                        method: get_names_method,
                        args: {
                            site_name: open_form.fields_dict.oc_site.value,
                            filter_name: request.term
                        },
                        callback: function(r) {
                            if (!r.exc && r.message) {
                                response(r.message);
                            } else {
                                response(false);
                            }
                        }
                    });
                }
            },
            select: function(event, ui) {
                field.$input.val(ui.item.value);
                field.$input.trigger("change");
                var open_form = frappe.ui.form.get_open_grid_form();
                var name = open_form.fields_dict[oc_field_name];
                var id = open_form.fields_dict[oc_field_id];
                frappe.call({
                    method: get_id_method,
                    args: {
                        site_name: open_form.fields_dict.oc_site.value,
                        name: name.value
                    },
                    callback: function(r) {
                        if(!r.exc && r.message) {
                            id.set_value(r.message);
                            id.refresh();
                        }
                    }
                });
            }
        }).on("focus", function() {
            setTimeout(function() {
                if(!field.$input.val()) {
                    field.$input.autocomplete("search", "");
                }
            }, 500);
        });
    }
}
