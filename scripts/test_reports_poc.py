"""Rollback-only aggregation/security checks for the isolated PoC site."""
import frappe
from rpm_worklog import reports
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected rejection')


def profile(name, **updates):
    values = dict(doctype=reports.CONFIG, report_title=name, enabled=1, grain='Log',
        group_field='work_date', operation='Sum', measure_field='total_hours',
        sort_order='Group Ascending', chart_type='bar', default_state='All')
    values.update(updates)
    return frappe.get_doc(values).insert().name

try:
    frappe.set_user('Administrator')
    users = frappe.get_all('Has Role', filters={'parenttype':'User', 'role':'RPM Work Log Pilot'}, pluck='parent')
    assert len(users) >= 2
    first, second = users[:2]
    emp1, emp2 = reports.employee_for(first), reports.employee_for(second)
    manager_emp = frappe.db.get_value('Employee',emp1,'reports_to')
    manager = frappe.db.get_value('Employee',manager_emp,'user_id')
    assert manager and 'RPM Work Log Manager Pilot' in frappe.get_roles(manager)
    # Ensure both test employees report to the test manager inside this transaction only.
    frappe.db.set_value('Employee',emp2,'reports_to',manager_emp)
    sums = profile('test log sums')
    entries = profile('test entry sums', grain='Entry', group_field='result', measure_field='hours')
    counts = profile('test counts', group_field='review_state', operation='Count', measure_field='')
    averages = profile('test averages', operation='Average')
    for i in range(302):
        name = 'rpm-report-test-' + frappe.generate_hash(length=16)
        owner, employee = (first,emp1) if i < 301 else (second,emp2)
        frappe.db.sql('INSERT INTO `tabRPM Daily Work Log` (name,owner,employee,work_date,total_hours,review_state,docstatus) VALUES (%s,%s,%s,%s,2,%s,0)',(name,owner,employee,'2090-01-01','Approved'))
        for hours in (0.5,1.5):
            frappe.db.sql('INSERT INTO `tabRPM Work Log Line` (name,parent,parenttype,parentfield,hours,result) VALUES (%s,%s,%s,%s,%s,%s)',(frappe.generate_hash(length=20),name,reports.PARENT,'lines',hours,'Completed'))
    def query(p=sums, scope='Self', state='All'):
        return reports.run(p,'2090-01-01','2090-01-01',scope,state)
    frappe.set_user(first)
    assert query()['rows'][0]['value'] == 602
    assert query()['sample_count'] == 301  # Not truncated to 300.
    assert query(entries)['rows'][0]['value'] == 602
    assert query(entries)['sample_count'] == 602
    assert query(counts)['rows'][0]['value'] == 301
    assert query(averages)['rows'][0]['value'] == 2
    assert query(state='Draft')['rows'] == []
    assert not frappe.has_permission(reports.CONFIG,'write')
    denied(lambda: query(scope='Team'))
    denied(lambda: reports.run(sums,'2090-01-01','2092-01-01'))
    denied(lambda: query(state="Approved' OR 1=1"))
    frappe.set_user(second)
    assert query()['sample_count'] == 1
    frappe.set_user(manager)
    assert query(scope='Team')['sample_count'] == 302
    assert query(scope='Team')['rows'][0]['value'] == 604
    frappe.db.set_value('Employee',emp1,'reports_to',None)
    assert query(scope='Team')['sample_count'] == 1
    frappe.set_user('Guest')
    denied(lambda: reports.options())
    denied(lambda: query())
    frappe.set_user('Administrator')
    doc = frappe.get_doc(reports.CONFIG, sums)
    doc.group_field = 'name` FROM tabUser --'
    denied(lambda: reports.validate_config(doc))
    doc.group_field = 'result'
    denied(lambda: reports.validate_config(doc))
    doc = frappe.get_doc(reports.CONFIG, entries)
    doc.measure_field = 'total_hours'
    denied(lambda: reports.validate_config(doc))
    field = frappe.get_meta(reports.PARENT).get_field('total_hours')
    previous = field.hidden
    try:
        field.hidden = 1
        denied(lambda: reports.validate_config(frappe.get_doc(reports.CONFIG, sums)))
    finally:
        field.hidden = previous
    print('REPORT_TEST_PASS: >300 complete aggregation, parent/entry grain, counts/average, self/team isolation, live Reports To, invalid metadata/input and guest denial')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
