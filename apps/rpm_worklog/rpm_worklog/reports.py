"""Allowlisted Work Log aggregation with live-scoped employee selection."""
import frappe
from frappe import _
from frappe.utils import getdate
from rpm_worklog.review import employee_for

PARENT = 'RPM Daily Work Log'
CHILD = 'RPM Work Log Line'
CONFIG = 'RPM Work Log Report'
STATES = ('Draft', 'Pending Review', 'Returned', 'Approved')
# New metadata fields require explicit review before entering this catalog.
FIELDS = {
    'work_date': (PARENT, 'Date'),
    'employee': (PARENT, 'Link'),
    'department': (PARENT, 'Link'),
    'review_state': (PARENT, 'Select'),
    'total_hours': (PARENT, 'Float'),
    'activity_type': (CHILD, 'Link'),
    'item_code': (CHILD, 'Link'),
    'result': (CHILD, 'Select'),
    'hours': (CHILD, 'Float'),
}


def catalog():
    result = {}
    for name, (doctype, kind) in FIELDS.items():
        field = frappe.get_meta(doctype).get_field(name)
        if field and not field.hidden and field.fieldtype == kind:
            result[name] = dict(label=_(field.label), grain='Log' if doctype == PARENT else 'Entry', type=kind)
    return result


def validate_config(doc, method=None):
    available = catalog()
    if doc.grain not in ('Log', 'Entry') or doc.operation not in ('Sum', 'Count', 'Average'):
        frappe.throw(_('Invalid report grain or operation'))
    group = available.get(doc.group_field)
    if not group or doc.group_field in ('hours', 'total_hours') or (doc.grain == 'Log' and group['grain'] != 'Log'):
        frappe.throw(_('Grouping field is unavailable or incompatible'))
    expected = 'total_hours' if doc.grain == 'Log' else 'hours'
    if doc.operation != 'Count' and (doc.measure_field != expected or expected not in available):
        frappe.throw(_('Measure is unavailable or incompatible with report grain'))
    if doc.operation == 'Count' and doc.measure_field:
        frappe.throw(_('Leave measure empty for Count'))
    if doc.chart_type not in ('bar', 'line', 'pie') or doc.sort_order not in ('Group Ascending', 'Value Descending'):
        frappe.throw(_('Invalid chart or sort order'))
    if doc.default_state not in ('All', *STATES):
        frappe.throw(_('Invalid review status'))
    if not (doc.report_title or '').strip():
        frappe.throw(_('Report title is required'))


def scopes():
    if frappe.session.user == 'Guest' or not frappe.db.get_value('User', frappe.session.user, 'enabled'):
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    roles = frappe.get_roles()
    employee_for(frappe.session.user)
    allowed = []
    if 'RPM Work Log Pilot' in roles:
        allowed.append('Self')
    if 'RPM Work Log Manager Pilot' in roles:
        allowed.append('Team')
    if not allowed:
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    return allowed


@frappe.whitelist()
def options():
    allowed = scopes()
    return dict(scopes=allowed, fields=catalog(), reports=frappe.get_all(CONFIG,
        filters={'enabled': 1}, fields=['name', 'report_title', 'default_state'], order_by='report_title', limit_page_length=0))


@frappe.whitelist()
def search_employees(scope='Team', text=''):
    if scope not in scopes():
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    me = employee_for(frappe.session.user)
    filters = {'status': 'Active'}
    if scope == 'Self':
        filters['name'] = me
    else:
        filters.update(reports_to=me, name=['!=', me])
    text = str(text or '').strip()[:100]
    # Escape LIKE wildcards; a typed % or _ is a literal, not a directory dump.
    pattern = '%' + text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    rows = frappe.get_all('Employee', filters=filters,
        or_filters=[[field, 'like', pattern] for field in ('employee_number', 'employee_name')],
        fields=['name', 'employee_number', 'employee_name'],
        order_by='employee_number, employee_name, name', limit_page_length=21)
    return dict(employees=[dict(value=r.name, label=employee_label(r)) for r in rows[:20]],
        has_more=len(rows) > 20)


def employee_label(row):
    return f"{row.employee_number or _('No employee number')} | {row.employee_name or _('Unnamed employee')}"


@frappe.whitelist()
def run(report, from_date, to_date, scope='Self', state='All', employee=None):
    if scope not in scopes():
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    if state not in ('All', *STATES):
        frappe.throw(_('Invalid review status'))
    if not from_date or not to_date:
        frappe.throw(_('Select a date range'))
    start, end = getdate(from_date), getdate(to_date)
    if not 0 <= (end - start).days <= 365:
        frappe.throw(_('Select at most 366 days'))
    doc = frappe.get_doc(CONFIG, report)
    if not doc.enabled:
        frappe.throw(_('Report is disabled'))
    validate_config(doc)  # Revalidate current metadata, even for existing saved profiles.
    me = employee_for(frappe.session.user)
    params = {'me': me, 'user': frappe.session.user, 'start': start, 'end': end, 'state': state}
    where = ['p.work_date BETWEEN %(start)s AND %(end)s', "COALESCE(p.docstatus,0) != 2"]
    if scope == 'Self':
        where.extend(['p.employee = %(me)s', 'p.owner = %(user)s'])
    else:
        where.extend(['e.reports_to = %(me)s', "e.status = 'Active'", 'e.name != %(me)s'])
    selected = None
    if employee:
        selected = frappe.db.get_value('Employee', employee,
            ['name', 'employee_number', 'employee_name', 'reports_to', 'status'], as_dict=True)
        permitted = selected and selected.status == 'Active' and (
            selected.name == me if scope == 'Self' else selected.reports_to == me and selected.name != me)
        if not permitted:
            frappe.throw(_('Not permitted'), frappe.PermissionError)
        params['employee'] = employee
        where.append('p.employee = %(employee)s')
    if state != 'All':
        where.append("COALESCE(NULLIF(p.review_state,''),'Draft') = %(state)s")
    alias = 'p' if FIELDS[doc.group_field][0] == PARENT else 'c'
    group = f'{alias}.`{doc.group_field}`'
    if doc.group_field == 'review_state':
        group = "COALESCE(NULLIF(p.review_state,''),'Draft')"
    # Every SQL identifier and operator comes from the validated static catalog above.
    measure = 'COUNT(*)' if doc.operation == 'Count' else (
        ('SUM' if doc.operation == 'Sum' else 'AVG') +
        ('(p.total_hours)' if doc.grain == 'Log' else '(c.hours)'))
    join = '' if doc.grain == 'Log' else f" INNER JOIN `tab{CHILD}` c ON c.parent=p.name AND c.parenttype='{PARENT}' AND c.parentfield='lines'"
    order = 'bucket ASC' if doc.sort_order == 'Group Ascending' else 'value DESC, bucket ASC'
    rows = frappe.db.sql(f"SELECT {group} AS bucket, {measure} AS value, COUNT(*) AS samples FROM `tab{PARENT}` p INNER JOIN `tabEmployee` e ON e.name=p.employee {join} WHERE {' AND '.join(where)} GROUP BY {group} ORDER BY {order}", params, as_dict=True)
    if len(rows) > 500:
        frappe.throw(_('More than 500 groups; narrow the date range'))
    available = catalog()
    labels = {}
    if doc.group_field == 'employee' and rows:
        labels = {r.name: employee_label(r) for r in frappe.get_all('Employee',
            filters={'name': ['in', [r.bucket for r in rows]]},
            fields=['name', 'employee_number', 'employee_name'], limit_page_length=0)}
    return dict(title=doc.report_title, grain=doc.grain, operation=doc.operation,
        group_label=available[doc.group_field]['label'], chart_type=doc.chart_type,
        scope=scope, from_date=str(start), to_date=str(end), state=state,
        employee_label=employee_label(selected) if selected else None,
        unit='records' if doc.operation == 'Count' else 'hours',
        rows=[dict(label=labels.get(r.bucket, str(r.bucket)) if r.bucket not in (None, '') else _('Not specified'), value=float(r.value or 0), samples=r.samples) for r in rows],
        sample_count=sum(r.samples for r in rows))
