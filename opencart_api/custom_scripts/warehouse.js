print_update_inventory_log = function(message) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Item Code</th><th>Bin Location</th><th>Barcode</th><th>Status</th>');

    for(var i=0; i < message.items.length; i++) {
        $tr = $('<tr>');
        $tr.append('<td>' + message.items[i].item_code + '</td>');
        $tr.append('<td>' + message.items[i].bin_location + '</td>');
        $tr.append('<td>' + message.items[i].barcode + '</td>');
        $tr.append('<td>' + message.items[i].status_message + '</td>');
        $tbody.append($tr);
    }

    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    // var $header = $('<h4>'+__("Sync Log: ")+'</h4>');
    // $panel.append($header);

    var $info = $('<p></p>').html('Processed ' + message.items.length + ' entries');
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['update_inventory_log'].wrapper).html(msg);
}


frappe.ui.form.on("Warehouse", "update_inventory", function(frm) {
    frappe.prompt([{label: "Use Item Code from Coulumn", fieldtype:"Data", default: "SKU"},
                   {label:"Bin Location of Bin", fieldtype:"Section Break"},
                   {label: "Update Bin Location", fieldtype:"Check", default: 1},
                   {fieldtype:"Column Break"},
                   {label: "Bin Location from Column", fieldtype:"Data", default: "Bin"},
                   {label:"Barcode of Item", fieldtype:"Section Break"},
                   {label: "Update Barcode", fieldtype:"Check", default: 1},
                   {fieldtype:"Column Break"},
                   {label: "Barcode from Column", fieldtype:"Data", default: "UPC"}
                   ],
        function(data) {
            $(cur_frm.fields_dict['update_inventory_log'].wrapper).html("");
            frappe.call({
                method:"opencart_api.warehouses.update_inventory",
                args: {
                    warehouse: frm.doc.name,
                    item_code_from: data.use_item_code_from_coulumn,
                    update_bin_location: data.update_bin_location,
                    bin_location_from: data.bin_location_from_column,
                    update_barcode: data.update_barcode,
                    barcode_from: data.barcode_from_column
                },
                callback: function(r) {
                    if(!r.exc) {
                        print_update_inventory_log(r.message);

                        // clean unused file data
                        frappe.call({
                            type: "GET",
                            args: {
                                cmd: "opencart_api.warehouses.clear_file_data",
                                name: frm.doc.name
                            },
                            callback: function(data) {
                            }
                        });
                    }
                }
            });
        }
    , __("Update Inventory from File"), __("Update"));
});
