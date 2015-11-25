
cur_frm.cscript.custom_refresh = function(doc, dt, dn) {
    if(!doc.__islocal) {
        frappe.call({
            method:"opencart_api.bins.get_warehouses",
            args: {
                "item_code": doc.item_code,
            },
            callback: function(r) {
                if(!r.exc) {
                    print_warehouses(r.message);
                }
            }
        });
        this.frm.add_custom_button(__('Sync from Opencart'), this.sync_item_from_opencart).addClass("btn-primary");
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
