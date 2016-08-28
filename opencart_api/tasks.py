from __future__ import unicode_literals
from datetime import datetime

import frappe
from frappe.utils.background_jobs import enqueue

from items import pull_products_from_oc
from item_groups import pull_categories_from_oc
import oc_api

import time
import MySQLdb


EMAIL_SENDER = "scheduler@abc.com"
EMAIL_SUBJECT = "[%s] Opencart syncing %s "


@frappe.whitelist()
def hourly():
    all_oc_sites = frappe.get_all('Opencart Site', fields=['name'])
    from orders import pull_added_from
    for oc_site in all_oc_sites:
        pull_added_from(oc_site.get('name'))


@frappe.whitelist()
def daily(site_name=None):
    # Get all oc sites
    if site_name:
        site_names = [[site_name]]
    else:
        site_names = frappe.db.sql("""select name from `tabOpencart Site`""")
    results = {}
    logs = ["<b>Sync Log on date: %s</b>" % datetime.now().strftime("%d-%b-%y")]
    success = True

    # Sync
    for name in site_names:
        name = name[0]
        logs.append("Opencart Site: %s" % name)
        site_doc = frappe.get_doc("Opencart Site", name)
        root_item_group = site_doc.get('root_item_group')
        opencart_api = oc_api.get(name)

        # Sync groups and record log
        logs.append("Sync Item Groups")
        group_results = pull_categories_from_oc(name, root_item_group, opencart_api, silent=True)
        results['groups'] = group_results
        # logs += results.get('logs')
        success = success and group_results.get('success')

        # Sync items and record log
        logs.append("Sync Items")
        item_results = pull_products_from_oc(name, root_item_group, opencart_api, silent=True)
        results['items'] = item_results
        # logs += results_item.get('logs')
        success = success and item_results.get('success')
        continue

        # Send mail if unsuccessful
        logs = ['<p>%s</p>' % x for x in logs]
        frappe.sendmail(recipients=[str(site_doc.get('user'))],
                        sender=EMAIL_SENDER,
                        subject=EMAIL_SUBJECT % (datetime.now().strftime("%d-%b-%y"), "succeeded" if success else "failed"), message='</br>'.join(logs))

    results['success'] = success
    return results


def on_bin_update_task(site, bin_name, actual_qty_diff, event):
    try:
        frappe.connect(site=site)
        from items import _on_bin_update
        for i in xrange(3):
            try:
                # _on_bin_update(bin_name, actual_qty_diff)
                enqueue(_on_bin_update, queue="default", timeout=300, event=event, bin_name=bin_name, actual_qty_diff=actual_qty_diff)
            except MySQLdb.OperationalError, e:
                # deadlock, try again
                if e.args[0] == 1213:
                    frappe.db.rollback()
                    time.sleep(1)
                    continue
                else:
                    raise
            else:
                break
    except:
        frappe.db.rollback()
        frappe.logger(__name__).error(frappe.get_traceback())
        frappe.db.commit()
        raise

    else:
        frappe.db.commit()

    finally:
        frappe.destroy()
