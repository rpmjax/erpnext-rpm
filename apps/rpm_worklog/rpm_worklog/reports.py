"""Allowlisted Work Log aggregation with live-scoped employee selection."""
import frappe
from frappe import _
from frappe.utils import getdate
from rpm_worklog.review import employee_for
from rpm_worklog.scope import analysis_scope
from rpm_worklog.analysis import options as analysis_options, search_filters
from rpm_worklog.identity import label as employee_label, FIELDS as IDENTITY_FIELDS

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


@frappe.whitelist()
def options():
    available = analysis_options()
    allowed = available["scopes"]
    return dict(scopes=allowed, company=available["company"], fields=catalog(), reports=frappe.get_all(CONFIG,
        filters={'enabled': 1}, fields=['name', 'report_title', 'default_state'], order_by='report_title', limit_page_length=0))


@frappe.whitelist()
def search_employees(scope='Team', text=''):
    candidates = search_filters(scope, 'employee', text)
    names = [r['value'] for r in candidates['items']]
    labels = {r.name:employee_label(r) for r in frappe.get_all('Employee',
        filters={'name':['in',names]},fields=IDENTITY_FIELDS,limit_page_length=0)} if names else {}
    return dict(employees=[dict(value=name,label=labels[name]) for name in names],
        has_more=candidates['has_more'])


@frappe.whitelist()
def run(report, from_date, to_date, scope='Self', state='All', employee=None):
    where, scope_params = analysis_scope(scope)
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
    params = {'start': start, 'end': end, 'state': state}
    params.update(scope_params)
    authorized_where = list(where)
    where.append('p.work_date BETWEEN %(start)s AND %(end)s')
    selected = None
    if employee:
        if not isinstance(employee,str) or len(employee)>140:
            frappe.throw(_('Not permitted'), frappe.PermissionError)
        # Validate selection with the same live business scope, without date filtering.
        permitted = frappe.db.sql("SELECT p.name FROM `tabRPM Daily Work Log` p "
            "JOIN `tabEmployee` e ON e.name=p.employee WHERE " + ' AND '.join(authorized_where) +
            " AND p.employee=%(selected)s LIMIT 1", {**scope_params,'selected':employee})
        if not permitted:
            frappe.throw(_('Not permitted'), frappe.PermissionError)
        selected = frappe.db.get_value('Employee',employee,IDENTITY_FIELDS,as_dict=True)
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
            fields=IDENTITY_FIELDS, limit_page_length=0)}
    return dict(title=doc.report_title, grain=doc.grain, operation=doc.operation,
        group_label=available[doc.group_field]['label'], chart_type=doc.chart_type,
        scope=scope, from_date=str(start), to_date=str(end), state=state,
        employee_label=employee_label(selected) if selected else None,
        unit='records' if doc.operation == 'Count' else 'hours',
        rows=[dict(label=labels.get(r.bucket, str(r.bucket)) if r.bucket not in (None, '') else _('Not specified'), value=float(r.value or 0), samples=r.samples) for r in rows],
        sample_count=sum(r.samples for r in rows))
