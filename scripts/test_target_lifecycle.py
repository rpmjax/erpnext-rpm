"""Rollback-only lifecycle checks on the explicitly disposable release fixture site.
Run with bench Python from sites, after target metadata installation.
"""
import frappe
from rpm_worklog import targets

frappe.init(site='analysis-fresh.internal')
frappe.connect()
assert frappe.conf.get('rpm_worklog_managed')

def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected rejection')

def log(target):
    return frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Lifecycle regression',
        employee='ARF-0',work_date='2090-01-01',lines=[dict(work_item='Fixture',hours=1.25,
        quantity=0,result='In Progress',work_target=target)])).insert()

try:
    assert frappe.get_meta(targets.DT).has_field('is_archived')
    frappe.set_user('Administrator')
    for i, role in [(0,'RPM Work Log Pilot'),(1,'RPM Work Log Manager Pilot')]:
        frappe.get_doc('User',f'analysis-release-{i}@example.invalid').add_roles(role)
    frappe.db.set_value('Employee','ARF-0','reports_to','ARF-1')
    owner='analysis-release-0@example.invalid'
    frappe.set_user(owner)
    t=frappe.get_doc(dict(doctype=targets.DT,target_name='Lifecycle fixture',status='Open')).insert()
    d=log(t.name)
    before=[(r.name,r.work_target,r.hours,r.quantity) for r in d.lines]
    for status, archived in [('Completed',0),('Closed',0),('Open',1),('Completed',1),('Closed',1)]:
        t.reload();t.status=status;t.is_archived=archived;t.save()
        d.reload();d.title='Existing links remain valid';d.save()
        assert [(r.name,r.work_target,r.hours,r.quantity) for r in d.lines]==before
        assert d.review_state=='Draft' and d.total_hours==1.25
        assert targets.summary(t.name)['total_hours']==1.25
        denied(lambda:log(t.name))
        d.reload();d.append('lines',dict(work_item='new row',hours=1,result='In Progress',work_target=t.name))
        denied(d.save)
    # Returned logs remain editable; Approved logs retain the existing review lock.
    frappe.db.set_value('RPM Daily Work Log',d.name,'review_state','Returned')
    d.reload();d.save();assert d.review_state=='Returned'
    frappe.db.set_value('RPM Daily Work Log',d.name,'review_state','Approved')
    d.reload();denied(d.save)
    frappe.db.set_value('RPM Daily Work Log',d.name,'review_state','Draft')
    t.reload();t.is_archived=0;t.status='Open';t.save()
    assert log(t.name).lines[0].work_target==t.name
    denied(lambda:frappe.get_doc(dict(doctype=targets.DT,target_name='forged legacy',status='Archived')).insert())
    t.status='Archived';denied(t.save)
    # Simulate pre-migration legacy data without guessing its outcome.
    frappe.db.set_value(targets.DT,t.name,{'status':'Archived','is_archived':1})
    t.reload();t.description='Keep legacy unknown';t.save()
    d.reload();d.save()
    t.is_archived=0;denied(t.save)
    t.reload();t.status='Completed';t.save()
    assert t.is_archived==1 and t.status=='Completed'
    frappe.set_user('analysis-release-1@example.invalid')
    assert frappe.get_doc(targets.DT,t.name).has_permission('read')
    denied(lambda:frappe.get_doc(targets.DT,t.name).save())
    frappe.set_user('Administrator')
    denied(lambda:frappe.get_doc(targets.DT,t.name).save())
    print('LIFECYCLE_PASS: retained existing links, new links denied, reopen, legacy, manager read-only, no admin bypass')
finally:
    frappe.db.rollback()
    frappe.destroy()
