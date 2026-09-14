import frappe
from rpm_worklog.review import transition
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
try:
 user=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')[0]
 frappe.set_user(user)
 emp=frappe.db.get_value('Employee',{'user_id':user},'name')
 doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Inline item test',work_date='2099-03-03',employee=emp,lines=[dict(item_code='RPM-POC-SHOCK',hours=1,result='Completed',quantity=5)])).insert()
 assert not doc.lines[0].work_item and doc.lines[0].item_name_snapshot
 doc.reload();assert doc.lines[0].item_code=='RPM-POC-SHOCK'
 transition(doc.name,'submit',doc.modified)
 meta=frappe.get_meta('RPM Work Log Line')
 assert meta.get_field('work_item').hidden and not meta.get_field('work_item').reqd
 assert not meta.get_field('item_code').read_only
 fields=[f.fieldname for f in meta.fields]
 assert fields.index('item_code') < fields.index('work_item')
 print('INLINE_ITEM_SAVE_SUBMIT_PASS without Work Item, snapshot, metadata order')
finally:
 frappe.db.rollback();frappe.set_user('Administrator')
