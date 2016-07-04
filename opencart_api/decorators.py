
def sync_to_opencart(fn):
    def sync_to_opencart_fn(doc, *args, **kwargs):
        if doc.get('oc_site') and doc.get('oc_sync_to'):
            if doc.get('oc_is_updating'):
                doc.update({'oc_is_updating': '0'})
                return
            return fn(doc, *args, **kwargs)
    return sync_to_opencart_fn


def sync_item_to_opencart(fn):
    def sync_to_opencart_fn(doc, *args, **kwargs):
        if doc.get('oc_sync_to'):
            if doc.get('oc_is_updating'):
                doc.update({'oc_is_updating': '0'})
                return
            return fn(doc, *args, **kwargs)
    return sync_to_opencart_fn
