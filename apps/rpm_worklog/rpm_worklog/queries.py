import frappe
from frappe.utils import getdate
from rpm_worklog.review import employee_for
from rpm_worklog.scope import employee_filters, log_scope
from rpm_worklog.identity import label, FIELDS as IDENTITY_FIELDS


@frappe.whitelist()
def defaults():
    employee_filters('Self')
    employee=employee_for(frappe.session.user)
    result = frappe.db.get_value('Employee',employee,IDENTITY_FIELDS + ['department'],as_dict=True)
    result['display_label'] = label(result)
    return result


@frappe.whitelist()
def daily_summary(work_date):
    where, params = log_scope('Self')
    params['date'] = getdate(work_date)
    rows=frappe.db.sql('SELECT p.total_hours FROM `tabRPM Daily Work Log` p INNER JOIN tabEmployee e ON e.name=p.employee WHERE '+ ' AND '.join(where) +' AND p.work_date=%(date)s',params,as_dict=True)
    return dict(count=len(rows),hours=sum(float(r.total_hours or 0) for r in rows))


@frappe.whitelist()
def team_summary(from_date=None,to_date=None,work_log=None):
    filters = employee_filters('Team')
    manager=employee_for(frappe.session.user)
    if not work_log:
        start,end=getdate(from_date),getdate(to_date)
        if not from_date or not to_date or not 0 <= (end-start).days <= 31:
            frappe.throw('Select a date range of at most 32 days')
    employees=frappe.get_all('Employee',filters=filters,fields=IDENTITY_FIELDS,limit_page_length=0)
    labels = {e.name:label(e) for e in employees}
    where, params = log_scope('Team')
    if work_log:
        where.append('p.name=%(work_log)s')
        params['work_log'] = work_log
    else:
        where.append('p.work_date BETWEEN %(start)s AND %(end)s')
        params.update(start=start,end=end)
    rows=frappe.db.sql('SELECT p.name,p.work_date,p.title,p.employee,p.employee_name,p.department,p.total_hours,p.review_state,p.modified FROM `tabRPM Daily Work Log` p INNER JOIN tabEmployee e ON e.name=p.employee WHERE '+ ' AND '.join(where) +' ORDER BY p.work_date DESC,p.name LIMIT 301',params,as_dict=True)
    for row in rows[:300]:
        row.employee_label = labels.get(row.employee, '未填姓名 | 未填工號')
        row.lines=frappe.get_all('RPM Work Log Line',filters={'parent':row.name,'parenttype':'RPM Daily Work Log','parentfield':'lines'},
            fields=['activity_type','work_item','item_code','item_name_snapshot','quantity','result','hours','note'],order_by='idx',limit_page_length=0)
    return dict(logs=rows[:300],truncated=len(rows)>300,direct_report_count=len(employees))


@frappe.whitelist()
def worklog_identity(name):
    doc = frappe.get_doc('RPM Daily Work Log', name)
    doc.check_permission('read')
    employee = frappe.db.get_value('Employee', doc.employee, IDENTITY_FIELDS, as_dict=True)
    return dict(employee=doc.employee, display_label=label(employee)) if employee else None
