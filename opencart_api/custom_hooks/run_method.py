from __future__ import unicode_literals
import json
import inspect
import frappe
from frappe import _
from frappe.utils import cint


from erpnext.stock.doctype.packing_slip.packing_slip import PackingSlip
from opencart_api.packing_slip import update_item_details


CLASS_METHODS_PATCHES = {
    'Packing Slip': {'update_item_details': [PackingSlip, update_item_details]}
}


@frappe.whitelist()
def runserverobj(method, docs=None, dt=None, dn=None, arg=None, args=None):
    """run controller method - old style"""
    if not args:
        args = arg or ""

    if dt:  # not called from a doctype (from a page)
        if not dn:
            dn = dt  # single
        doc = frappe.get_doc(dt, dn)

    else:
        doc = frappe.get_doc(json.loads(docs))
        doc._original_modified = doc.modified
        doc.check_if_latest()

    if not doc.has_permission("read"):
        frappe.msgprint(_("Not permitted"), raise_exception=True)

    if doc:
        try:
            args = json.loads(args)
        except ValueError:
            args = args

        # patching class methods
        if CLASS_METHODS_PATCHES.get(doc.doctype):
            for patch_method, patch_refs in CLASS_METHODS_PATCHES.get(doc.doctype).items():
                setattr(patch_refs[0], patch_method, patch_refs[1])

        fnargs, varargs, varkw, defaults = inspect.getargspec(getattr(doc, method))
        if not fnargs or (len(fnargs) == 1 and fnargs[0] == "self"):
            r = doc.run_method(method)

        elif "args" in fnargs or not isinstance(args, dict):
            r = doc.run_method(method, args)

        else:
            r = doc.run_method(method, **args)

        if r:
            #  build output as csv
            if cint(frappe.form_dict.get('as_csv')):
                make_csv_output(r, doc.doctype)
            else:
                frappe.response['message'] = r

        frappe.response.docs.append(doc)


def make_csv_output(res, dt):
    """send method response as downloadable CSV file"""
    import frappe

    from cStringIO import StringIO
    import csv

    f = StringIO()
    writer = csv.writer(f)
    for r in res:
        row = []
        for v in r:
            if isinstance(v, basestring):
                v = v.encode("utf-8")
            row.append(v)
        writer.writerow(row)

    f.seek(0)

    frappe.response['result'] = unicode(f.read(), 'utf-8')
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = dt.replace(' ', '')
