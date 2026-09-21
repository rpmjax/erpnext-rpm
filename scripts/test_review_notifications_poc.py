"""Rollback-only in-app notification routing, transaction and no-email checks."""
import frappe
from unittest.mock import patch
from rpm_worklog import review, notifications, queries
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def logs(name):
    return frappe.get_all('Notification Log',filters={'document_name':name,'type':notifications.TYPE},
        fields=['name','for_user','link','source_name','title'],order_by='creation')


try:
    employee,manager='j250301@outlook.com','t870602rpm@outlook.com'
    frappe.set_user('Administrator')
    for user in (employee,manager):
        if frappe.db.exists('Notification Settings',user):
            frappe.db.set_value('Notification Settings',user,'enabled',1)
    frappe.set_user(employee)
    doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='notification test',
        employee=review.employee_for(employee),work_date='2090-01-01',
        lines=[dict(work_item='test',hours=1,result='Completed')])).insert()
    assert not logs(doc.name)
    with patch('frappe.sendmail',side_effect=AssertionError('Must not send email')):
        review.transition(doc.name,'submit',str(doc.modified))
        first=logs(doc.name)
        assert len(first)==1 and first[0].for_user==manager
        assert 'rpm-team-work-log-viewer' in first[0].link and 'work_date=2090-01-01' in first[0].link
        event=frappe.get_doc('RPM Work Log Review Event',first[0].source_name)
        notifications.notify_review(doc,event,manager)
        assert len(logs(doc.name))==1
        frappe.set_user(manager)
        detail = queries.team_summary(work_log=doc.name, from_date='2000-01-01', to_date='2000-01-01')
        assert len(detail['logs']) == 1 and detail['logs'][0].name == doc.name
        assert detail['logs'][0].review_state == 'Pending Review' and len(detail['logs'][0].lines) == 1
        assert not queries.team_summary(work_log='missing-log')['logs']
        original_manager = frappe.db.get_value('Employee', doc.employee, 'reports_to')
        frappe.db.set_value('Employee', doc.employee, 'reports_to', None)
        assert not queries.team_summary(work_log=doc.name)['logs']
        frappe.db.set_value('Employee', doc.employee, 'reports_to', original_manager)
        doc.reload()
        review.transition(doc.name,'return',str(doc.modified),'correct this')
        assert logs(doc.name)[-1].for_user==employee
        assert logs(doc.name)[-1].link.endswith('/'+doc.name)
        frappe.set_user(employee)
        doc.reload()
        rows=[{'name':doc.name,'modified':str(doc.modified)}]*2
        result=review.bulk_submit(rows)
        assert result['counts']['success']==1 and result['counts']['skipped']==1
        assert len(logs(doc.name))==3 and logs(doc.name)[-1].title=='工作紀錄重新送審'
        # Roll back a successful approval; its notification must disappear too.
        frappe.db.savepoint('notification_rollback')
        frappe.set_user(manager)
        doc.reload()
        review.transition(doc.name,'approve',str(doc.modified))
        assert len(logs(doc.name))==4 and logs(doc.name)[-1].for_user==employee
        frappe.db.rollback(save_point='notification_rollback')
        assert len(logs(doc.name))==3
        doc.reload()
        review.transition(doc.name,'approve',str(doc.modified))
        assert len(logs(doc.name))==4
    frappe.set_user('j220402rpm@outlook.com')
    assert not frappe.get_list('Notification Log',filters={'document_name':doc.name})
    assert 'RPM Work Log Review' in frappe.get_hooks('notification_skip_email_types')
    print('NOTIFICATIONS_PASS: submit/return/resubmit/approve recipients, routes, dedupe, bulk skip, rollback, isolation, no email')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
