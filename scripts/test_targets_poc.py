"""Rollback-only target permissions and optional linking regression."""
import frappe
from rpm_worklog import targets
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected rejection')


def target(title='test target'):
    return frappe.get_doc(dict(doctype=targets.DT, target_name=title, status='Open')).insert()


def log(employee, work_target=None):
    return frappe.get_doc(dict(doctype='RPM Daily Work Log', title='target test',
        employee=employee,work_date='2090-01-01',lines=[dict(work_item='test task',
        hours=1,result='In Progress',work_target=work_target)])).insert()


try:
    first, second, manager = 'j250301@outlook.com','j220402rpm@outlook.com','t870602rpm@outlook.com'
    frappe.set_user(first)
    t = target()
    unused = target('unused deletion test')
    emp = targets.employee_for(first)
    assert t.employee == emp and t.owner == first
    assert t.has_permission('write')
    no_link = log(emp)
    linked = log(emp,t.name)
    assert no_link.total_hours == linked.total_hours == 1
    frappe.set_user(second)
    denied(lambda: frappe.delete_doc(targets.DT,unused.name))
    denied(lambda: frappe.get_doc(targets.DT,t.name).check_permission('read'))
    assert not frappe.get_list(targets.DT,filters={'name':t.name})
    denied(lambda: log(targets.employee_for(second),t.name))
    frappe.set_user(manager)
    denied(lambda: frappe.delete_doc(targets.DT,unused.name))
    assert frappe.get_doc(targets.DT,t.name).has_permission('read')
    assert frappe.get_list(targets.DT,filters={'name':t.name})
    denied(lambda: frappe.get_doc(targets.DT,t.name).save())
    denied(target)
    frappe.set_user('Administrator')
    frappe.db.set_value('Employee',emp,'reports_to',None)
    frappe.set_user(manager)
    denied(lambda: frappe.get_doc(targets.DT,t.name).check_permission('read'))
    assert not frappe.get_list(targets.DT,filters={'name':t.name})
    frappe.set_user(first)
    frappe.delete_doc(targets.DT,unused.name)
    assert not frappe.db.exists(targets.DT,unused.name)
    t = frappe.get_doc(targets.DT,t.name)
    t.employee = targets.employee_for(second)
    denied(t.save)
    t = frappe.get_doc(targets.DT,t.name)
    t.start_date='2090-02-01'
    t.due_date='2090-01-01'
    denied(t.save)
    t = frappe.get_doc(targets.DT,t.name)
    t.status='Archived'
    t.save()
    linked.reload()
    linked.title='retained historical target'
    linked.save()
    denied(lambda: log(emp,t.name))
    denied(lambda: frappe.delete_doc(targets.DT,t.name))
    frappe.db.set_value('RPM Daily Work Log',linked.name,'docstatus',2)
    denied(lambda: frappe.delete_doc(targets.DT,t.name))
    frappe.set_user('Guest')
    denied(lambda: frappe.get_doc(targets.DT,t.name).check_permission('read'))
    print('TARGET_TEST_PASS: own create/edit, optional link, cross-owner denial, live manager read-only, dates, immutable ownership, archive retention')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
