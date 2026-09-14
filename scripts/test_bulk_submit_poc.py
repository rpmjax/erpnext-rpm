import frappe
from rpm_worklog.review import bulk_submit, transition
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
def create(user):
 frappe.set_user(user)
 emp=frappe.db.get_value('Employee',{'user_id':user},'name')
 return frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Bulk rollback test',employee=emp,work_date='2099-04-01',lines=[dict(hours=1,result='Completed')])).insert()
def record(doc):return {'name':doc.name,'modified':frappe.db.get_value(doc.doctype,doc.name,'modified')}
try:
 users=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')
 a=create(users[0]); b=create(users[0]); invalid=create(users[0]);stale=create(users[0]); foreign=create(users[1])
 frappe.set_user(users[0]); transition(b.name,'submit',record(b)['modified'])
 frappe.db.set_value('RPM Work Log Line',invalid.lines[0].name,'hours',0)
 bad_version=record(stale);bad_version['modified']='2000-01-01 00:00:00'
 records=[record(a),record(b),record(invalid),bad_version,record(foreign),record(a)]
 out=bulk_submit(records)
 assert out['counts']=={'success':1,'skipped':2,'failed':3},out
 assert frappe.db.get_value(a.doctype,a.name,'review_state')=='Pending Review'
 assert frappe.db.get_value(invalid.doctype,invalid.name,'review_state')=='Draft'
 assert not frappe.db.exists('RPM Work Log Review Event',{'work_log':invalid.name})
 assert not frappe.db.exists('RPM Work Log Review Event',{'work_log':foreign.name})
 again=bulk_submit([record(a)]);assert again['counts']['skipped']==1
 assert frappe.db.count('RPM Work Log Review Event',{'work_log':a.name})==1
 print('BULK_PASS mixed valid/pending/invalid/stale/foreign/duplicate, no failed residue, retry idempotent')
finally:
 frappe.db.rollback();frappe.set_user('Administrator')
