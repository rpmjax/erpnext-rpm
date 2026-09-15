"""Rollback-only smoke test on a new managed site. Never run on a populated site."""
import frappe
from rpm_worklog.bootstrap import enroll
from rpm_worklog import queries, reports, review
assert frappe.conf.get('rpm_worklog_managed') and not frappe.db.count('RPM Daily Work Log')
assert not frappe.db.count('Employee'), 'Only use on the disposable installation test'
frappe.local.lang = 'en'
try:
    if not frappe.db.exists('Warehouse Type','Transit'):
        frappe.get_doc(dict(doctype='Warehouse Type',name='Transit')).insert()
    company=frappe.get_doc(dict(doctype='Company',company_name='Install Test',abbr='INT',default_currency='TWD',country='Taiwan')).insert()
    if not frappe.db.exists('Gender','Male'):
        frappe.get_doc(dict(doctype='Gender',gender='Male')).insert()
    users=[]
    for index in range(3):
        email=f'install-test-{index}@example.invalid'
        user=frappe.get_doc(dict(doctype='User',email=email,first_name=f'Test {index}',enabled=1,user_type='System User',send_welcome_email=0)).insert()
        employee=frappe.get_doc(dict(doctype='Employee',first_name=f'Test {index}',employee_number=f'TEST-{index}',company=company.name,user_id=email,gender='Male',date_of_birth='1990-01-01',date_of_joining='2026-01-01',status='Active')).insert()
        users.append((email,employee.name))
    for user,employee in users[1:]: frappe.db.set_value('Employee',employee,'reports_to',users[0][1])
    enroll(users[0][0],manager=True)
    enroll(users[1][0]); enroll(users[2][0])
    # Re-enrollment must not duplicate self permissions.
    enroll(users[1][0])
    assert frappe.db.count('User Permission',{'user':users[1][0],'allow':'Employee'})==1
    frappe.set_user(users[1][0])
    assert queries.defaults().name==users[1][1]
    log=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Fresh install smoke',employee=users[1][1],work_date='2026-09-15',lines=[dict(hours=1.25,result='Completed'),dict(hours=.75,result='Completed')])).insert()
    assert log.total_hours == 2
    assert queries.daily_summary('2026-09-15')['hours']==2
    assert reports.run('rpm-work_date','2026-09-15','2026-09-15')['rows'][0]['value']==2
    review.transition(log.name,'submit',log.modified)
    frappe.set_user(users[2][0])
    assert not frappe.has_permission(log.doctype,'read',doc=log.name)
    assert queries.daily_summary('2026-09-15')['count']==0
    frappe.set_user(users[0][0])
    assert queries.team_summary('2026-09-15','2026-09-15')['logs'][0].name==log.name
    assert reports.run('rpm-work_date','2026-09-15','2026-09-15','Team')['rows'][0]['value']==2
    current=frappe.get_doc(log.doctype,log.name)
    review.transition(log.name,'return',current.modified,'Please correct')
    frappe.set_user(users[1][0])
    current=frappe.get_doc(log.doctype,log.name)
    current.lines[0].hours=1.5
    current.save()
    review.transition(log.name,'submit',current.modified)
    frappe.set_user(users[0][0])
    current=frappe.get_doc(log.doctype,log.name)
    review.transition(log.name,'approve',current.modified)
    assert len(review.history(log.name))==4
    print('MANAGED_INSTALL_SMOKE_PASS: enrollment, defaults, save, self isolation, team, analytics, return/resubmit/approve')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
