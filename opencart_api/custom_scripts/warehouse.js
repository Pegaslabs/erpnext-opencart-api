
frappe.ui.form.on("Warehouse", "update_inventory", function(frm) {
    frappe.prompt({label:"Warehouse", fieldtype:"Link", options:"Warehouse", reqd: 1},
        function(data) {
            frappe.call({
                method:"opencart_api.warehouses.update_inventory",
                args: {
                    doc_name: frm.doc.name
                },
                callback: function(r) {
                    var items = [];
                    frm.clear_table("items");
                    for(var i=0; i< r.message.length; i++) {
                        var d = frm.add_child("items");
                        $.extend(d, r.message[i]);
                    }
                    frm.refresh_field("items");
                }
            });
        }
    , __("Update Inventory from File"), __("Update"));
});
