print_sync_log_warehouses = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Opencart Warehouse ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        if (o[6]) {
            $tr.append('<td>'+o[6]+'</td>');
        }
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Warehouse Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.add_count || message.update_count || message.skip_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' warehouses: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All warehouses are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['warehouse_sync_log'].wrapper).html(msg);
}

print_sync_log_stores = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Opencart Store ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        if (o[6]) {
            $tr.append('<td>'+o[6]+'</td>');
        }
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Store Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.add_count || message.update_count || message.skip_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' stores: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All stores are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['store_sync_log'].wrapper).html(msg);
}

print_sync_log_item_prices = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Item Code</th><th>Price List</th><th>Currency</th><th>Rate</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tr.append('<td>'+o[7]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Item Price Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.add_count || message.update_count || message.skip_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' item prices: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All item prices are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['item_price_sync_log'].wrapper).html(msg);
}

print_sync_log_item_attributes = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Opencart Option ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        if (o[6]) {
            $tr.append('<td>'+o[6]+'</td>');
        }
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Item attributes Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.add_count || message.update_count || message.skip_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' item attributes: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All item attributes are up to date. Checked ' + message.check_count + ' item attributes </p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['item_attributes_sync_log'].wrapper).html(msg);
}

print_sync_log_cat = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Parent Name</th><th>Opencart Category ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        if (o[6]) {
            $tr.addClass(o[6]);
        }
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tr.append('<td>'+o[7]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Group Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.check_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' categories: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All item groups are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['group_sync_log'].wrapper).html(msg);
}

print_sync_log_item = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Item Code</th><th>Item Group Name</th><th>Opencart Product ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(message.results, function(o){
        $tr = $('<tr>');
        // Add class
        if (o[6]) {
            $tr.addClass(o[6]);
        }
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tr.append('<td>'+o[7]+'</td>');
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
    $(cur_frm.fields_dict['item_sync_log'].wrapper).html(msg);
}

print_sync_log_customer_groups = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Parent Customer Group</th><th>Opencart Customer Group ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tr.append('<td>'+o[7]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Customer Group Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.check_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count + ' customer groups: ' + message.add_count + ' - added, ' + message.update_count + ' - updated, ' + message.skip_count + ' - skipped.');
    }
    else {
        $info = $('<p>All customer groups are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['customer_group_sync_log'].wrapper).html(msg);
}

print_sync_log_customers = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Opencart Customer ID</th><th>Customer Group</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        if (o[7]) {
            $tr.append('<td>'+o[7]+'</td>');
        }
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Customer Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.add_count || message.update_count || message.skip_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count +' customers, Added ' + message.add_count +' customers, Updated ' + message.update_count + ' customers, Skipped ' + message.skip_count + ' customers');
    }
    else {
        $info = $('<p>All Customers are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['customers_sync_log'].wrapper).html(msg);
}

print_sync_log_orders = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Opencart Order ID</th><th>Last Sync</th><th>Last Modified</th><th>Status</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        if (o[6]) {
            $tr.append('<td>'+o[6]+'</td>');
        }
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Order Sync Log: ")+'</h4>');
    $panel.append($header);

    var $info;
    if (message.check_count) {
        $info = $('<p></p>').html('Checked ' + message.check_count +' orders, Added ' + message.add_count +' orders, Updated ' + message.update_count + ' orders, Skipped ' + message.skip_count + ' orders');
    }
    else {
        $info = $('<p>All Orders are up to date</p>');
    }
    $panel.append($info);
    $panel.append($table);
    var msg = $('<div>').append($panel).html();
    $(cur_frm.fields_dict['orders_sync_log'].wrapper).html(msg);
}

print_children_group = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.item_groups.get_child_groups",
            item_group_name: doc.root_item_group
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_cat(data.message);
            }
        }
    });
}

print_related_stores = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.oc_stores.get_oc_related_stores",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_stores(data.message);
            }
        }
    });
}

cur_frm.cscript.refresh = function(doc, dt, dn) {

    var $msg = $('<div></div>');
    $msg.append('<h4>'+ 'Before you proceed, make sure that you have:' +'</h4>');
    $msg.append('<p>'+ ' - set Default Price List for each Customer Group' +'</p>');
    $msg.append('<p>'+ ' - specified Opencart Customer Group Rules for each Customer Group if needed' +'</p>');
    $msg.append('<p>'+ ' - specified Shipping Rule for each Opencart Store' +'</p>');
    $msg.append('<p>'+ ' - assigned Customer Group for each Opencart Store' +'</p>');
    $(cur_frm.fields_dict['order_notice'].wrapper).html($msg.html());

    frappe.call({
        type: "GET",
        args: {
            cmd: "opencart_api.oc_site.clear_file_data",
            site_name: doc.name
        },
        callback: function(data) {
        }
    });
}

cur_frm.cscript.root_item_group = function(doc, dt, dn) {
    // Get all its child group to
    //print_children_group(doc, dt, dn);
}

cur_frm.cscript.sync_item_with_oc_site = function(doc, dt, dn) {
    // TODO: Give some warnings if some categories already has an opencart site
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.items.sync_all_items",
            api_map: doc.api_map,
            site_name: doc.name,
            header_key: doc.opencart_header_key,
            header_value: doc.opencart_header_value,
            server_base_url: doc.server_base_url
        },
        callback: function(data) {
            if (data && data.message) {
                // print_sync_log_cat(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_warehouses_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.warehouses.pull",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_warehouses(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_stores_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.oc_stores.pull",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_stores(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_item_prices_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.item_prices.pull",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_item_prices(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_item_attributes_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.item_attributes.pull",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_item_attributes(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_item_groups_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.item_groups.pull_categories_from_oc",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_cat(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_items_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.items.pull_products_from_oc",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_item(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_items_from_inventory_spreadsheet = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.items.pull_from_inventory_spreadsheet",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_item(data.message, true);

                // clean unused file data
                frappe.call({
                    type: "GET",
                    args: {
                        cmd: "opencart_api.oc_site.clear_file_data",
                        site_name: doc.name
                    },
                    callback: function(data) {
                    }
                });
            }
        }
    });

}

cur_frm.cscript.pull_customer_groups_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.customer_groups.pull",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_customer_groups(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_customers_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.customers.pull_customers_from_oc",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_customers(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_orders_from_oc_site = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.orders.pull_orders_from_oc",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_orders(data.message, true);
            }
        }
    });
}

cur_frm.cscript.pull_orders_modified_from = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.orders.pull_added_from",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_orders(data.message, true);
            }
        }
    });
}

cur_frm.cscript.test_connection = function(doc, dt, dn) {
    frappe.call({
        freeze: true,
        type: "GET",
        args: {
            cmd: "opencart_api.oc_site.test_connection",
            site_name: doc.name
        },
        callback: function(data) {
            if (data && data.message && data.message.rest_api && data.message.rest_admin_api) {
                if (data.message.rest_api.success && data.message.rest_admin_api.success) {
                    msgprint(__("Connections to Opencart Rest API and REST Admin API are successful"));
                } else if (data.message.rest_api.success) {
                    msgprint(__("Cannot connect to Opencart REST Admin API: " + data.message.rest_admin_api.error));
                } else if (data.message.rest_admin_api.success) {
                    msgprint(__("Cannot connect to Opencart REST API: " + data.message.rest_api.error));
                } else {
                    msgprint(__("Cannot connect to Opencart REST Admin API: " + data.message.rest_admin_api.error + "\n" 
                        + "Cannot connect to Opencart REST API: " + data.message.rest_api.error));
                }
            }
        }
    });
}
