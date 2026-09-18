"""Rollback-only target totals, pagination, review transitions and authorization."""
import frappe
from rpm_worklog import targets, review
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected rejection')


def make_log(employee, target, hours, date='2090-01-01'):
    return frappe.get_doc(dict(doctype='RPM Daily Work Log',title='summary test',employee=employee,
        work_date=date,lines=[dict(work_item='<b>text</b>',hours=hours,result='In Progress',work_target=target)])).insert()


def act(doc, action, reason=None):
    doc.reload()
    review.transition(doc.name, action, str(doc.modified), reason)


try:
    first, second, manager = 'j250301@outlook.com','j220402rpm@outlook.com','t870602rpm@outlook.com'
    frappe.set_user(first)
    emp = review.employee_for(first)
    t = frappe.get_doc(dict(doctype=targets.DT,target_name='summary test',status='Open')).insert()
    assert targets.summary(t.name)['entry_count'] == 0
    draft = make_log(emp,t.name,1.25)
    draft.append('lines',dict(work_item='same target',hours=0.75,result='Completed',work_target=t.name))
    draft.append('lines',dict(work_item='unrelated',hours=9,result='Completed'))
    draft.save()
    pending = make_log(emp,t.name,3,'2090-01-02')
    returned = make_log(emp,t.name,4,'2090-01-03')
    approved = make_log(emp,t.name,5,'2090-01-04')
    for doc in (pending,returned,approved):
        act(doc,'submit')
    frappe.set_user(manager)
    act(returned,'return','test correction')
    act(approved,'approve')
    data = targets.summary(t.name)
    assert data['total_hours'] == 14 and data['log_count'] == 4 and data['entry_count'] == 5
    assert {s:v['hours'] for s,v in data['totals'].items()} == {'Draft':2,'Pending Review':3,'Returned':4,'Approved':5,'Other':0}
    assert not data['can_open_log']
    detail = targets.worklog_detail(t.name,draft.name)
    assert len(detail.lines) == 3 and detail.total_hours == 11
    assert sum(bool(row.linked_to_target) for row in detail.lines) == 2
    frappe.set_user(first)
    assert targets.summary(t.name)['can_open_log']
    # Actual review transition must rebucket, never add a second copy of hours.
    act(returned,'submit')
    data = targets.summary(t.name)
    assert data['total_hours'] == 14 and data['totals']['Returned']['hours'] == 0
    assert data['totals']['Pending Review']['hours'] == 7
    # Corrupt/cancelled/other-parent fixtures are excluded even if a link is present.
    cancelled = make_log(emp,t.name,6)
    frappe.db.set_value('RPM Daily Work Log',cancelled.name,'docstatus',2)
    frappe.set_user(second)
    other = make_log(review.employee_for(second),None,7)
    frappe.db.set_value('RPM Work Log Line',other.lines[0].name,'work_target',t.name)
    denied(lambda: targets.summary(t.name))
    denied(lambda: targets.worklog_detail(t.name,draft.name))
    frappe.set_user(first)
    assert targets.summary(t.name)['total_hours'] == 14
    denied(lambda: targets.worklog_detail(t.name,other.name))
    denied(lambda: targets.worklog_detail(t.name,cancelled.name))
    # More than a page: aggregation must include rows not returned in this page.
    for idx in range(53):
        frappe.db.sql('''INSERT INTO `tabRPM Work Log Line`
            (name,parent,parenttype,parentfield,idx,work_target,hours,result)
            VALUES (%s,%s,'RPM Daily Work Log','lines',%s,%s,0.25,'Completed')''',
            (frappe.generate_hash(length=20),draft.name,idx+4,t.name))
    first_page, second_page = targets.summary(t.name), targets.summary(t.name,50)
    assert first_page['total_hours'] == second_page['total_hours'] == 27.25
    assert first_page['entry_count'] == 58 and first_page['log_count'] == 4
    assert len(first_page['rows']) == 50 and len(second_page['rows']) == 8
    ids = lambda page: {(r.work_log,r.entry_index) for r in page['rows']}
    assert not (ids(first_page) & ids(second_page))
    assert len(targets.summary(t.name,100)['rows']) == 0
    denied(lambda: targets.summary(t.name,-1))
    denied(lambda: targets.summary(t.name,'0 OR 1=1'))
    t.status='Archived'
    t.save()
    assert targets.summary(t.name)['total_hours'] == 27.25
    frappe.set_user('Administrator')
    frappe.db.set_value('Employee',emp,'reports_to',None)
    frappe.set_user(manager)
    denied(lambda: targets.summary(t.name))
    denied(lambda: targets.worklog_detail(t.name,draft.name))
    frappe.set_user('Administrator')
    frappe.db.set_value('User',first,'enabled',0)
    frappe.set_user(first)
    denied(lambda: targets.summary(t.name))
    frappe.set_user('Guest')
    denied(lambda: targets.summary(t.name))
    denied(lambda: targets.worklog_detail(t.name,draft.name))
    print('TARGET_SUMMARY_PASS: entry-grain totals, review rebucketing, full aggregation with paging, archive, cancellation and live access denial')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
