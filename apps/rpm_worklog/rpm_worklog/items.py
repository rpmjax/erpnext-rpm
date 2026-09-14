import math
import frappe
from frappe import _


def allowed_user():
    if frappe.session.user != 'Administrator' and ('RPM Work Log Pilot' not in frappe.get_roles() or not frappe.db.exists('Employee', {'user_id':frappe.session.user,'status':'Active'})):
        frappe.throw(_('Not permitted'), frappe.PermissionError)


def item_data(code):
    item = frappe.db.get_value('Item', code, ['name','item_name','stock_uom','disabled','has_variants'], as_dict=True)
    if not item or item.disabled or item.has_variants:
        frappe.throw(_('Select an enabled item or a specific item variant'))
    units = {item.stock_uom: 1.0}
    for u in frappe.get_all('UOM Conversion Detail', filters={'parent':code,'parenttype':'Item'},fields=['uom','conversion_factor']):
        factor = float(u.conversion_factor or 0)
        if u.uom != item.stock_uom and math.isfinite(factor) and factor > 0:
            units[u.uom] = factor
    return item, units


@frappe.whitelist()
def search_items(text=''):
    allowed_user()
    text = str(text or '').strip()[:100]
    # Literal substring matching, bounded response, no prices or inventory details.
    pattern = '%' + text.replace('\\','\\\\').replace('%','\\%').replace('_','\\_') + '%'
    return frappe.get_all('Item', filters={'disabled':0,'has_variants':0},
        or_filters=[['name','like',pattern],['item_name','like',pattern]],
        fields=['name','item_name'],order_by='name',limit_page_length=20)


def validate_items(doc):
    old = {}
    if not doc.is_new():
        old = {r.name:r for r in frappe.get_all('RPM Work Log Line', filters={'parent':doc.name,'parenttype':doc.doctype},fields=['name','item_code','item_name_snapshot'])}
    for row in doc.lines:
        if not row.item_code:
            row.item_name_snapshot = None
            row.item_stock_uom = None
            row.item_conversion_factor = None
            continue
        item, units = item_data(row.item_code)
        previous = old.get(row.name)
        row.item_name_snapshot = previous.item_name_snapshot if previous and previous.item_code == row.item_code and previous.item_name_snapshot else item.item_name
        if not (row.work_item or '').strip(): row.work_item = item.item_name
        # Units temporarily disabled: do not fill, convert, or overwrite stored unit values.
