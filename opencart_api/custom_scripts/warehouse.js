
print_update_inventory_log = function(message) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Item Code</th><th>Item Group Name</th><th>Opencart Product ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');

                    // var items = [];
                    // frm.clear_table("items");
                    // for(var i=0; i< r.message.length; i++) {
                    //     var d = frm.add_child("items");
                    //     $.extend(d, r.message[i]);
                    // }
                    // frm.refresh_field("items");

    for(var i=0; i< r.message.length; i++) {
        $tr = $('<tr>');
        $tr.append('<td>'+r.message[i].item_code+'</td>');
        // $tr.append('<td>'+o[1]+'</td>');
        // $tr.append('<td>'+o[2]+'</td>');
        // $tr.append('<td>'+o[3]+'</td>');
        // $tr.append('<td>'+o[4]+'</td>');
        // $tr.append('<td>'+o[7]+'</td>');
        $tbody.append($tr);
    });

    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Item Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.check_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' products: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All products are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['update_inventory_log'].wrapper).html(msg);


frappe.ui.form.on("Warehouse", "update_inventory", function(frm) {
    frappe.prompt({label:"Warehouse", fieldtype:"Link", options:"Warehouse", reqd: 1},
        function(data) {
            $(cur_frm.fields_dict['update_inventory_log'].wrapper).html("");
            frappe.call({
                method:"opencart_api.warehouses.update_inventory",
                args: {
                    doc_name: frm.doc.name
                },
                callback: function(r) {

                    if(!r.exc) {
                        print_update_inventory_log(r.message)
                    }
                }
            });
        }
    , __("Update Inventory from File"), __("Update"));
});
