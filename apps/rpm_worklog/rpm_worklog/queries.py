import frappe
from frappe.utils import getdate
from rpm_worklog.review import employee_for


@frappe.whitelist()
def defaults():
    if 'RPM Work Log Pilot' not in frappe.get_roles():
        frappe.throw('Employee role required',frappe.PermissionError)
    employee=employee_for(frappe.session.user)
    return frappe.db.get_value('Employee',employee,['name','department','employee_name'],as_dict=True)


@frappe.whitelist()
def daily_summary(work_date):
    employee=defaults().name
    rows=frappe.get_all('RPM Daily Work Log',filters={'employee':employee,'owner':frappe.session.user,'work_date':getdate(work_date)},fields=['total_hours'],limit_page_length=0)
    return dict(count=len(rows),hours=sum(float(r.total_hours or 0) for r in rows))


@frappe.whitelist()
def team_summary(from_date,to_date):
    if 'RPM Work Log Manager Pilot' not in frappe.get_roles():
        frappe.throw('Manager role required',frappe.PermissionError)
    manager=employee_for(frappe.session.user)
    start,end=getdate(from_date),getdate(to_date)
    if not from_date or not to_date or not 0 <= (end-start).days <= 31:
        frappe.throw('Select a date range of at most 32 days')
    employees=frappe.get_all('Employee',filters={'reports_to':manager,'status':'Active','name':['!=',manager]},pluck='name')
    rows=frappe.get_all('RPM Daily Work Log',filters={'employee':['in',employees],'work_date':['between',[start,end]]},
        fields=['name','work_date','title','employee','employee_name','department','total_hours','review_state','modified'],order_by='work_date desc, name',limit_page_length=301) if employees else []
    for row in rows[:300]:
        row.lines=frappe.get_all('RPM Work Log Line',filters={'parent':row.name,'parenttype':'RPM Daily Work Log','parentfield':'lines'},
            fields=['activity_type','work_item','item_code','item_name_snapshot','quantity','result','hours','note'],order_by='idx',limit_page_length=0)
    return dict(logs=rows[:300],truncated=len(rows)>300,direct_report_count=len(employees))
