"""Single-employee projection of the authorized stored work-line dataset."""
from decimal import Decimal
import frappe
from rpm_worklog.analysis import source_query
from rpm_worklog.scope import analysis_scope
from rpm_worklog.review import employee_for
from rpm_worklog.identity import label, FIELDS

REPORT = 'rpm-employee-work-time-distribution'


@frappe.whitelist()
def query(from_date, to_date, scope='Self', state='All', employee=None):
    where, params = analysis_scope(scope)
    if state not in ('All', 'Draft', 'Pending Review', 'Returned', 'Approved'):
        frappe.throw('Invalid review status')
    if scope == 'Self':
        me = employee_for(frappe.session.user)
        if employee and employee != me:
            frappe.throw('Not permitted', frappe.PermissionError)
        employee = me
    if not isinstance(employee, str) or not employee or len(employee) > 140:
        frappe.throw('Select one employee')
    if scope != 'Self':
        permitted = frappe.db.sql('SELECT p.name FROM `tabRPM Daily Work Log` p '
            'JOIN `tabEmployee` e ON e.name=p.employee WHERE ' + ' AND '.join(where)
            + ' AND p.employee=%(selected)s LIMIT 1', {**params, 'selected': employee})
        if not permitted:
            frappe.throw('Not permitted', frappe.PermissionError)
    source, params, filters = source_query(scope, dict(from_date=from_date,
        to_date=to_date, employee=employee, review_state=state))
    # HEX preserves case and trailing spaces regardless of site collation.
    # NULL and empty activity share the unclassified bucket; work_item keeps NULL distinct.
    rows = frappe.db.sql("""SELECT HEX(COALESCE(c.activity_type,'')) AS activity_key,
        HEX(c.work_item) AS item_key, SUM(c.hours) AS hours, COUNT(*) AS line_count
        """ + source + ' GROUP BY activity_key,item_key', params, as_dict=True)
    buckets = {}
    for row in rows:
        activity = bytes.fromhex(row.activity_key).decode('utf-8')
        item = None if row.item_key is None else bytes.fromhex(row.item_key).decode('utf-8')
        buckets.setdefault(activity, []).append(dict(work_item=item,
            hours=Decimal(str(row.hours or 0)), line_count=int(row.line_count)))
    total = sum((x['hours'] for items in buckets.values() for x in items), Decimal(0))
    groups = []
    for activity, items in buckets.items():
        items.sort(key=lambda x: (-x['hours'], x['work_item'] is not None, x['work_item'] or ''))
        hours = sum((x['hours'] for x in items), Decimal(0))
        groups.append(dict(activity_type=activity or None, display_label=activity or '未分類',
            hours=float(hours), percentage=float(hours / total * 100) if total else 0,
            line_count=sum(x['line_count'] for x in items),
            top_items=[{**x, 'hours':float(x['hours'])} for x in items[:5]],
            remaining=dict(distinct_item_count=max(0,len(items)-5),
                line_count=sum(x['line_count'] for x in items[5:]),
                hours=float(sum((x['hours'] for x in items[5:]), Decimal(0))))))
    groups.sort(key=lambda x: (-x['hours'], x['activity_type'] or ''))
    person = frappe.db.get_value('Employee', employee, FIELDS, as_dict=True)
    return dict(contract_version=1, scope=scope, employee=dict(name=employee,label=label(person)),
        from_date=filters['from_date'], to_date=filters['to_date'], review_state=state,
        totals=dict(reported_hours=float(total), line_count=sum(g['line_count'] for g in groups),
            activity_type_count=sum(bool(g['activity_type']) for g in groups),
            unclassified_line_count=sum(g['line_count'] for g in groups if not g['activity_type'])),
        groups=groups)
