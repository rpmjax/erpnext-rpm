import frappe
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
try:
 user=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')[0]
 frappe.set_user(user)
 emp=frappe.db.get_value('Employee',{'user_id':user},'name')
 for legacy in (0,1):
  doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Quantity flag paused test',work_date='2099-03-02',employee=emp,lines=[dict(work_item='Test',hours=1,result='Completed',quantity=5,record_quantity=legacy)])).insert()
  doc.reload();assert doc.lines[0].record_quantity==legacy and doc.lines[0].quantity==5
  doc.lines[0].quantity=0;doc.save();doc.reload();assert doc.lines[0].record_quantity==legacy
 assert frappe.get_meta('RPM Work Log Line').get_field('record_quantity').hidden
 print('QUANTITY_FLAG_PAUSED_PASS no autoflag, previous value retained, 5/0 save, hidden')
finally:
 frappe.db.rollback();frappe.set_user('Administrator')
