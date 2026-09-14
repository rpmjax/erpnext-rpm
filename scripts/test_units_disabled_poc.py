import frappe
from rpm_worklog.review import transition
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
try:
 user=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')[0]
 frappe.set_user(user)
 emp=frappe.db.get_value('Employee',{'user_id':user},'name')
 doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Units disabled rollback test',work_date='2099-03-01',employee=emp,lines=[dict(work_item='Assembly',hours=1,result='Completed',quantity=5,item_code='RPM-POC-SHOCK')])).insert()
 assert not doc.lines[0].uom and doc.lines[0].quantity==5
 doc.lines[0].quantity=0;doc.save();assert not doc.lines[0].uom
 doc.lines[0].uom='PoC Piece';doc.save();doc.reload();assert doc.lines[0].uom=='PoC Piece'
 transition(doc.name,'submit',doc.modified)
 for field in ['uom','item_stock_uom','item_conversion_factor']:
  assert frappe.get_meta('RPM Work Log Line').get_field(field).hidden
 print('UNITS_DISABLED_PASS quantity 5/0 without units, no autofill, legacy unit retained, submit succeeds, fields hidden')
finally:
 frappe.db.rollback();frappe.set_user('Administrator')
