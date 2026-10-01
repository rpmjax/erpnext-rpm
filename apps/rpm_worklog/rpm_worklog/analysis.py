"""Versioned, read-only work-line dataset. All SQL identifiers are allowlisted."""
from datetime import date, datetime, timedelta
from decimal import Decimal
import frappe
from frappe.utils import getdate
from rpm_worklog.scope import analysis_scope

CONTRACT_VERSION = 1
PARENT_FIELDS = ('title','work_date','employee','employee_name','department','return_reason')
LINE_FIELDS = ('activity_type','work_item','result','note','hours','start_time','end_time',
    'quantity','uom','record_quantity','item_code','item_name_snapshot','item_stock_uom',
    'item_conversion_factor','work_target')
COLUMNS = ('work_log', *PARENT_FIELDS, 'review_state', 'employee_number',
    'current_company','current_manager_employee','line_id','line_index', *LINE_FIELDS)
STATE = "COALESCE(NULLIF(p.review_state,''),'Draft')"
FILTER_FIELDS = {'employee':'p.employee','department':'p.department','review_state':STATE,
    'activity_type':'c.activity_type','result':'c.result','work_target':'c.work_target'}


@frappe.whitelist()
def options():
    """Only advertise scopes this session can actually resolve."""
    allowed = []
    for candidate in ('Self','Team','Organization'):
        try:
            analysis_scope(candidate)
            allowed.append(candidate)
        except (frappe.PermissionError, frappe.ValidationError):
            # Avoid returning internal errors as popups for non-applicable scopes.
            frappe.clear_messages()
    if not allowed:
        frappe.throw('No Worklog analysis scope is available', frappe.PermissionError)
    return dict(scopes=allowed,company=frappe.conf.get('rpm_worklog_company') if 'Organization' in allowed else None)


def _filters(filters):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    if not isinstance(filters, dict) or set(filters) - {'from_date','to_date',*FILTER_FIELDS}:
        frappe.throw('Invalid analysis filters')
    if not filters.get('from_date') or not filters.get('to_date'):
        frappe.throw('Select a date range')
    start, end = getdate(filters['from_date']), getdate(filters['to_date'])
    if not 0 <= (end-start).days <= 365:
        frappe.throw('Select at most 366 days')
    result = {'from_date':str(start),'to_date':str(end)}
    for key in FILTER_FIELDS:
        value = filters.get(key)
        if value is None or value == '':
            continue
        if key in ('employee','department') and isinstance(value,list):
            if len(value)>100 or any(not isinstance(v,str) or not v or len(v)>140 for v in value):
                frappe.throw('Choose at most 100 valid filter values')
            if value:
                result[key]=list(dict.fromkeys(value))
            continue
        if not isinstance(value, str) or len(value) > 140:
            frappe.throw('Invalid analysis filter value')
        if key == 'review_state':
            if value == 'All':
                continue
            if value not in ('Draft','Pending Review','Returned','Approved'):
                frappe.throw('Invalid review status')
        result[key] = value
    return result


@frappe.whitelist()
def search_filters(scope='Self',kind='employee',text=''):
    """Candidates from authorized saved logs, independent of date filters."""
    where,params=analysis_scope(scope)
    if kind not in ('employee','department') or not isinstance(text,str) or len(text)>100:
        frappe.throw('Invalid candidate search')
    params['pattern']='%'+text.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    source=' FROM `tabRPM Daily Work Log` p JOIN `tabEmployee` e ON e.name=p.employee WHERE '
    if kind=='employee':
        where.append('(e.employee_number LIKE %(pattern)s OR e.employee_name LIKE %(pattern)s OR p.employee_name LIKE %(pattern)s OR e.name LIKE %(pattern)s)')
        select='SELECT DISTINCT e.name AS value,e.employee_name,e.employee_number'
        order='e.employee_number,e.employee_name,e.name'
    else:
        where.extend(["COALESCE(p.department,'')!=''",'p.department LIKE %(pattern)s'])
        select='SELECT DISTINCT p.department AS value'
        order='p.department'
    rows=frappe.db.sql(select+source+' AND '.join(where)+' ORDER BY '+order+' LIMIT 21',params,as_dict=True)
    return dict(items=[dict(value=r.value,label=(f"{r.employee_name or '未填姓名'}｜{r.employee_number or '未填工號'}｜{r.value}" if kind=='employee' else r.value)) for r in rows[:20]],has_more=len(rows)>20)


def _integer(value, minimum, maximum):
    if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
        frappe.throw('Invalid pagination')
    number = int(value)
    if not minimum <= number <= maximum:
        frappe.throw('Invalid pagination')
    return number


def _value(value):
    if isinstance(value, (date, datetime, timedelta)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


@frappe.whitelist()
def query(scope='Self', filters=None, offset=0, page_size=100):
    return dataset(scope, filters, offset, page_size)


def dataset(scope, filters, offset=0, page_size=100, complete=False):
    """Shared dataset for screen and synchronous complete export (one request)."""
    where, params = analysis_scope(scope)
    filters = _filters(filters)
    offset = _integer(offset, 0, 2147483647)
    page_size = _integer(page_size, 1, 1000)
    params.update(start=filters['from_date'], end=filters['to_date'], offset=offset, limit=page_size)
    where.append('p.work_date BETWEEN %(start)s AND %(end)s')
    for key, expression in FILTER_FIELDS.items():
        if key in filters:
            params['filter_'+key] = filters[key]
            operator='IN' if isinstance(filters[key],list) else '='
            where.append(f'{expression} {operator} %(filter_{key})s')
    source = '''FROM `tabRPM Daily Work Log` p
        INNER JOIN `tabEmployee` e ON e.name=p.employee
        INNER JOIN `tabRPM Work Log Line` c ON c.parent=p.name
          AND c.parenttype='RPM Daily Work Log' AND c.parentfield='lines'
        WHERE ''' + ' AND '.join(where)
    totals = frappe.db.sql('''SELECT COUNT(*) AS total_rows,
        COUNT(DISTINCT p.name) AS total_logs, COALESCE(SUM(c.hours),0) AS reported_hours '''
        + source, params, as_dict=True)[0]
    if complete and totals.total_rows > 50000:
        frappe.throw('More than 50000 work entries; narrow the date range before export')
    select = ['p.name AS work_log', *['p.'+f for f in PARENT_FIELDS], STATE+' AS review_state',
        'e.employee_number','e.company AS current_company','e.reports_to AS current_manager_employee',
        'c.name AS line_id','c.idx AS line_index', *['c.'+f for f in LINE_FIELDS]]
    pagination = '' if complete else ' LIMIT %(limit)s OFFSET %(offset)s'
    rows = frappe.db.sql('SELECT '+','.join(select)+' '+source+
        ' ORDER BY p.work_date,p.name,c.idx,c.name'+pagination,params,as_dict=True)
    return dict(contract_version=CONTRACT_VERSION, scope=scope, filters=filters,
        columns=list(COLUMNS), rows=[{key:_value(row[key]) for key in COLUMNS} for row in rows],
        total_rows=int(totals.total_rows), total_logs=int(totals.total_logs),
        reported_hours=float(totals.reported_hours), offset=offset,page_size=page_size,
        has_more=offset+len(rows)<totals.total_rows)
