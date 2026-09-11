import frappe
from frappe.boot import get_bootinfo
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
manager=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Manager Pilot'},pluck='parent')[0]
emp=frappe.db.get_value('Employee',{'user_id':manager},'name')
script=frappe.get_doc('Server Script','RPM Team Work Logs')
try:
    frappe.set_user(manager)
    frappe.local.form_dict=frappe._dict(from_date='2026-09-01',to_date='2026-09-30',manager='forged')
    script.execute_method()
    logs=frappe.response['message']['logs']; assert logs
    for log in logs:
        assert frappe.db.get_value('Employee',log.employee,'reports_to')==emp
        assert not frappe.has_permission('RPM Daily Work Log','write',doc=log.name)
    boot=get_bootinfo()
    assert any(i.label=='直屬員工工作紀錄' for i in boot.desktop_icons)
    selected=logs[0]
    frappe.set_user('Administrator')
    frappe.db.set_value('Employee',selected.employee,'reports_to',None)
    frappe.set_user(manager)
    script.execute_method()
    assert selected.name not in [r.name for r in frappe.response['message']['logs']]
    frappe.local.form_dict['name']=selected.name
    script.execute_method(); assert not frappe.response['message']['logs']
    print('Manager direct reports, live reassignment, forged target, read-only, boot icon PASS')
    users=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')
    for u in users:
        frappe.set_user(u)
        try: script.execute_method()
        except frappe.ValidationError: pass
        else: raise AssertionError('Employee endpoint access accepted')
    print('Employee denied manager endpoint PASS')
    print('TEAM_VIEWER_TEST_PASS')
finally:
    frappe.db.rollback();frappe.set_user('Administrator')
