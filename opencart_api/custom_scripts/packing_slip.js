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
