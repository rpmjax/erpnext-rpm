"""Rollback-only checks on the disposable release site; never run on business sites."""
import frappe
from rpm_worklog import activity_distribution as service

frappe.init(site='analysis-fresh.internal')
frappe.connect()
assert frappe.conf.get('rpm_worklog_managed')

def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected denial')

try:
    frappe.set_user('Administrator')
    frappe.get_doc('User', 'analysis-release-0@example.invalid').add_roles('RPM Work Log Pilot')
    frappe.get_doc('User', 'analysis-release-1@example.invalid').add_roles('RPM Work Log Manager Pilot')
    frappe.db.set_value('Employee', 'ARF-0', 'reports_to', 'ARF-1')
    for n in range(2):
        frappe.db.sql("""INSERT INTO `tabRPM Daily Work Log`
            (name,owner,employee,work_date,total_hours,review_state,docstatus)
            VALUES (%s,%s,'ARF-0','2090-01-01',999,%s,0)""",
            (f'DIST-{n}', 'analysis-release-0@example.invalid', 'Draft' if n == 0 else 'Approved'))
    for i in range(1100):
        text = ['momo', 'MOMO', 'momo ', '<script>', 'A', 'B', 'C'][i % 7]
        frappe.db.sql("""INSERT INTO `tabRPM Work Log Line`
            (name,parent,parenttype,parentfield,activity_type,work_item,hours)
            VALUES (%s,%s,'RPM Daily Work Log','lines',%s,%s,0.1)""",
            (f'DIST-L-{i}', f'DIST-{i % 2}', None if i < 10 else '配送', text))
    frappe.set_user('analysis-release-0@example.invalid')
    def query(**kwargs):
        return service.query('2090-01-01', '2090-01-01', **kwargs)
    d = query()
    assert d['totals'] == dict(reported_hours=110.0, line_count=1100,
        activity_type_count=1, unclassified_line_count=10)
    assert sum(g['hours'] for g in d['groups']) == 110
    for g in d['groups']:
        assert abs(sum(x['hours'] for x in g['top_items']) + g['remaining']['hours'] - g['hours']) < 1e-8
        assert sum(x['line_count'] for x in g['top_items']) + g['remaining']['line_count'] == g['line_count']
        assert len(g['top_items']) + g['remaining']['distinct_item_count'] == 7
    assert abs(sum(g['percentage'] for g in d['groups']) - 100) < 1e-8
    # Two original text values remain distinct; blank activity never drops their hours.
    frappe.db.sql("""INSERT INTO `tabRPM Daily Work Log`
        (name,owner,employee,work_date,total_hours,review_state,docstatus)
        VALUES ('DIST-EMPTY','analysis-release-0@example.invalid','ARF-0','2090-02-01',8.4,'Draft',0)""")
    for n, value, hours in [(0,None,8),(1,'',.4)]:
        frappe.db.sql("""INSERT INTO `tabRPM Work Log Line`
            (name,parent,parenttype,parentfield,activity_type,work_item,hours)
            VALUES (%s,'DIST-EMPTY','RPM Daily Work Log','lines',%s,%s,%s)""",
            (f'DIST-E-{n}', None if n==0 else '', value, hours))
    empty=service.query('2090-02-01','2090-02-01')
    assert empty['totals']['reported_hours']==8.4 and empty['totals']['activity_type_count']==0
    assert empty['groups'][0]['percentage']==100 and empty['groups'][0]['display_label']=='未分類'
    assert [x['work_item'] for x in empty['groups'][0]['top_items']]==[None,'']
    assert query(state='Approved')['totals']['line_count'] == 550
    assert service.query('2090-01-02','2090-01-02')['groups'] == []
    denied(lambda: service.query('2090-01-02','2090-01-01'))
    denied(lambda: service.query('2080-01-01','2090-01-01'))
    frappe.db.set_value('RPM Daily Work Log','DIST-0','docstatus',2)
    assert query()['totals']['line_count'] == 550
    frappe.db.set_value('RPM Daily Work Log','DIST-0','docstatus',0)
    frappe.db.sql("UPDATE `tabRPM Work Log Line` SET hours=0 WHERE parent IN ('DIST-0','DIST-1')")
    zero=query()
    assert zero['totals']['line_count']==1100 and all(g['percentage']==0 for g in zero['groups'])
    frappe.db.sql("UPDATE `tabRPM Work Log Line` SET hours=0.1 WHERE parent IN ('DIST-0','DIST-1')")
    denied(lambda: query(employee='ARF-1'))
    denied(lambda: query(scope='Team', employee='ARF-0'))
    denied(lambda: query(state='invalid'))
    denied(lambda: query(employee=['ARF-0']))
    frappe.set_user('analysis-release-1@example.invalid')
    denied(lambda: query(scope='Team'))
    denied(lambda: query(scope='Team', employee='ARF-1'))
    assert query(scope='Team', employee='ARF-0')['totals']['reported_hours'] == 110
    frappe.db.set_value('Employee','ARF-0','status','Left')
    denied(lambda: query(scope='Team',employee='ARF-0'))
    frappe.set_user('Administrator')
    frappe.get_doc('User','analysis-release-1@example.invalid').add_roles('RPM Worklog Management')
    frappe.set_user('analysis-release-1@example.invalid')
    frappe.conf.rpm_worklog_company = frappe.db.get_value('Employee','ARF-1','company')
    assert query(scope='Organization',employee='ARF-0')['totals']['line_count']==1100
    denied(lambda: query(scope='Organization'))
    frappe.db.set_value('Employee','ARF-0','company','Other company')
    denied(lambda: query(scope='Organization',employee='ARF-0'))
    frappe.conf.rpm_worklog_company = None
    denied(lambda: query(scope='Organization',employee='ARF-0'))
    frappe.db.set_value('User','analysis-release-1@example.invalid','enabled',0)
    denied(lambda: query(scope='Team',employee='ARF-0'))
    frappe.set_user('Guest')
    denied(query)
    print('ACTIVITY_DISTRIBUTION_PASS: scope, exact text groups, >1000 lines, reconciliation, review, single employee')
finally:
    frappe.db.rollback()
    frappe.destroy()
