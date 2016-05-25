
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

    // set_autocomplete_field("Opencart Product", "category");
    // set_autocomplete_field("Opencart Product", "manufacturer");
    // set_autocomplete_field("Opencart Product", "stock_status");
    // set_autocomplete_field("Opencart Product", "tax_class");
    cur_frm.cscript.init_oc_products();
}

cur_frm.cscript.oc_site = function(doc, cdt, cdn) {
//     var open_form = frappe.ui.form.get_open_grid_form();
//     if(open_form) {
//         var fields = ["category", "manufacturer", "stock_status", "tax_class"];
//         fields.forEach(function(entry) {
//             var oc_field_name = "oc_" + entry + "_name";
//             var oc_field_id = "oc_" + entry + "_id";
//             open_form.fields_dict[oc_field_name].set_value("");
//             open_form.fields_dict[oc_field_id].set_value("");
//         });
//         open_form.fields_dict["oc_sync_from"].set_model_value(1);
//         open_form.fields_dict["oc_sync_to"].set_model_value(1);
//     }
    cur_frm.cscript.render_product_details(doc, cdt, cdn);
}

cur_frm.cscript.render_product_details = function(doc, cdt, cdn) {
    var open_form = frappe.ui.form.get_open_grid_form();
    var oc_site = open_form.fields_dict["oc_site"].value;
    if(open_form && oc_site) {
        if(cur_frm.oc_products_raw_ready) {
            var product_details = cur_frm.oc_products_raw[oc_site] || {};
            if(product_details.success) {
                var data_html = frappe.render_template("opencart_product_data", product_details);
                $(open_form.fields_dict["data_html"].$wrapper).html(data_html);


                var links_html = frappe.render_template("opencart_product_links", product_details);
                var links_html_field = $(open_form.fields_dict["links_html"].$wrapper);
                links_html_field.html(links_html);

                // manufacturer
                links_html_field.find('input[data-fieldname="manufacturer"]').tagsinput({
                    typeahead: {
                        afterSelect: function(val) { this.$element.val(""); },
                        source: product_details.manufacturer_names || [],
                        showHintOnFocus: true
                    },
                    maxTags: 1,
                    minLength: 0,
                    freeInput: false,
                    trimValue: true
                });

                // category_names
                links_html_field.find('input[data-fieldname="category_names"]').tagsinput({
                    typeahead: {
                        afterSelect: function(val) { this.$element.val(""); },
                        source: product_details.category_names || [],
                        showHintOnFocus: true
                    },
                    maxTags: 20,
                    minLength: 0,
                    freeInput: false,
                    trimValue: true
                });

                // attribute section
                var attribute_html = frappe.render_template("opencart_product_attribute", product_details);
                var attribute_html_field = $(open_form.fields_dict["attribute_html"].$wrapper);
                attribute_html_field.html(attribute_html);
                attribute_html_field.find('input.attribute').typeahead({
                    source: product_details.attribute_names || [],
                    showHintOnFocus: true
                });
                attribute_html_field.on('click', '.btn-add', function(e)
                {
                    e.preventDefault();
                    var controlForm = $(this).closest('table'),
                        currentEntry = $(this).parents('tr:first'),
                        newEntry = $(currentEntry.clone()).appendTo(controlForm);

                    newEntry.find('input').val('')
                    newEntry.find('input.attribute').typeahead({
                        source: product_details.attribute_names || [],
                        showHintOnFocus: true
                    });
                    controlForm.find('tr:not(:last) .btn-add')
                        .removeClass('btn-add').addClass('btn-remove')
                        .removeClass('btn-success').addClass('btn-danger')
                        .html('<span class="glyphicon glyphicon-minus gs"></span>');
                }).on('click', '.btn-remove', function(e)
                {
                    $(this).parents('tr:first').remove();
                    e.preventDefault();
                    return false;
                });
            }
        } else {
            frappe.msgprint("Initial data is not loaded yet. Please wait a while and try again.");
        }
    }
}


set_autocomplete_field = function(input_field) {
    // var oc_field_name = "oc_" + field_name + "_name";
    // var oc_field_id = "oc_" + field_name + "_id";
    // var get_names_method = "opencart_api.items.get_" + field_name + "_names";
    // var get_id_method = "opencart_api.items.get_" + field_name + "_id";
    // var df = frappe.meta.get_docfield(doctype, oc_field_name, cur_frm.docname);
    // $(field.input_area).addClass("ui-front");
    input_field.autocomplete({
        minLength: 0,
        source: function(request, response) {
            response(["AAAA", "BBBB"]);
            // var open_form = frappe.ui.form.get_open_grid_form();
            // var id = open_form.fields_dict[oc_field_id];
            // if(request) {
            //     id.set_value("");
            //     id.refresh();
            // }
            // frappe.call({
            //     method: get_names_method,
            //     args: {
            //         site_name: open_form.fields_dict.oc_site.value,
            //         filter_term: request.term
            //     },
            //     callback: function(r) {
            //         if (!r.exc && r.message) {
            //             response(r.message);
            //         } else {
            //             response(false);
            //         }
            //     }
            // });
        },
        select: function(event, ui) {
            input_field.val(ui.item.value);
            input_field.trigger("change");
            input_field.trigger(jQuery.Event( 'keydown', { which: $.ui.keyCode.ENTER } ));
            // var open_form = frappe.ui.form.get_open_grid_form();
            // var name = open_form.fields_dict[oc_field_name];
            // var id = open_form.fields_dict[oc_field_id];
            // frappe.call({
            //     method: get_id_method,
            //     args: {
            //         site_name: open_form.fields_dict.oc_site.value,
            //         name: name.value
            //     },
            //     callback: function(r) {
            //         if(!r.exc && r.message) {
            //             id.set_value(r.message);
            //             id.refresh();
            //         }
            //     }
            // });
        }
    }).on("focus", function() {
        setTimeout(function() {
            if(!input_field.val()) {
                input_field.autocomplete("search", "");
            }
        }, 500);
    });
}

cur_frm.cscript.oc_products_on_form_rendered = function(doc, cdt, cdn) {
//     var open_form = frappe.ui.form.get_open_grid_form();
//     if(open_form) {
//         if(!open_form.fields_dict["oc_model"].value) {
//             open_form.fields_dict["oc_model"].set_value(cdn);
//         }
//         if(!open_form.fields_dict["oc_sku"].value) {
//             open_form.fields_dict["oc_sku"].set_value(cdn);
//         }
//     }
    cur_frm.cscript.render_product_details(doc, cdt, cdn);
}

cur_frm.cscript.oc_products_on_form_hide = function(doc, cdt, cdn) {
    var product_details_to_update = {};
    var open_form = frappe.ui.form.get_open_grid_form();
    if(open_form) {
        $(open_form.fields_dict["data_html"].$wrapper).find("input").each(function(){
            var fieldname = $(this).attr("data-fieldname");
            if(fieldname) {
                product_details_to_update[fieldname] = $(this).val();
            }
        });
        $(open_form.fields_dict["links_html"].$wrapper).find("input").each(function(){
            var fieldname = $(this).attr("data-fieldname");
            if(fieldname) {
                product_details_to_update[fieldname] = $(this).val();
            }
        });

        // attributes
        var attribute_html_field = $(open_form.fields_dict["attribute_html"].$wrapper);
        var attributes_values = [];
        attribute_html_field.find('tr').each(function () {
            var name = $(this).find('input.attribute').val();
            var text = $(this).find('input.text').val();
            attributes_values.push({"name": name, "text": text})
        });
        product_details_to_update["attributes_values"] = attributes_values;

        open_form.fields_dict["product_details_to_update"].set_model_value(JSON.stringify(product_details_to_update));
    }
}

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

cur_frm.cscript.init_oc_products = function () {
    cur_frm.oc_products_raw_ready = false;
    cur_frm.oc_products_raw = {};
    frappe.call({
        type: "GET",
        method: "opencart_api.items.get_oc_products_raw",
        args: {
            item_code: cur_frm.doc.name
        },
        callback: function(r) {
          if(!r.exc && r.message) {
              cur_frm.oc_products_raw = r.message;
              cur_frm.oc_products_raw_ready = true;
          }
        }
    });
}
