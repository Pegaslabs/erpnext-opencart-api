
cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
    if(!doc.__islocal) {
        frappe.call({
            method:"opencart_api.bins.get_inventory_per_warehouse",
            args: {
                "item_code": doc.item_code,
            },
            callback: function(r) {
                if(!r.exc && r.message) {
                    var inventories_html = frappe.render_template("inventory_per_warehouse", {"inventories": r.message || []});
                    $(cur_frm.fields_dict['warehouses'].wrapper).html(inventories_html);
                }
            }
        });
        this.frm.add_custom_button(__('Sync from Opencart'), this.sync_item_from_opencart).addClass("btn-primary");
    }
    cur_frm.cscript.init_oc_products();
}

cur_frm.cscript.oc_site = function(doc, cdt, cdn) {
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

                // product_store
                links_html_field.find('input[data-fieldname="store_names"]').tagsinput({
                    typeahead: {
                        afterSelect: function(val) { this.$element.val(""); },
                        source: product_details.store_names || [],
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

cur_frm.cscript.oc_products_on_form_rendered = function(doc, cdt, cdn) {
    cur_frm.cscript.render_product_details(doc, cdt, cdn);
}

cur_frm.cscript.oc_products_on_form_hide = function(doc, cdt, cdn) {
    var product_details_to_update = {};
    if(cur_frm.oc_products_raw_ready) {
        var open_form = frappe.ui.form.get_open_grid_form();
        var oc_site = open_form.fields_dict["oc_site"].value;
        if(open_form && oc_site) {
            var product_details = cur_frm.oc_products_raw[oc_site] || {};
            if(product_details.success) {
                $(open_form.fields_dict["data_html"].$wrapper).find("input, select").each(function() {
                    var fieldname = $(this).attr("data-fieldname");
                    if(fieldname) {
                        product_details_to_update[fieldname] = $(this).val();
                    }
                });

                $(open_form.fields_dict["links_html"].$wrapper).find("input").each(function() {
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
    }
}

cur_frm.cscript.sync_item_from_opencart = function(label, status) {
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

            var oc_discounts_html = frappe.render_template("opencart_discounts", {"oc_products_raw": cur_frm.oc_products_raw});
            $(cur_frm.fields_dict['oc_discounts'].wrapper).html(oc_discounts_html);
          }
        }
    });
}
