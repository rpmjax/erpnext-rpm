import frappe
from rpm_worklog.items import search_items
from rpm_worklog.review import transition
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
def denied(fn):
    try:fn()
    except (frappe.ValidationError,frappe.PermissionError):return
    raise AssertionError('Expected rejection')
try:
    group=frappe.db.get_value('Item Group',{'is_group':0},'name') or 'All Item Groups'
    code='RPM-ROLLBACK-ITEM'
    item=frappe.get_doc(dict(doctype='Item',item_code=code,item_name='Material selection test',item_group=group,stock_uom='PoC Piece',is_stock_item=0)).insert()
    user=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')[0]
    frappe.set_user(user)
    matches=search_items('RPM-ROLLBACK');assert len(matches)==1
    assert set(matches[0])=={'name','item_name','stock_uom'}
    employee=frappe.db.get_value('Employee',{'user_id':user},'name')
    doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Item rollback',employee=employee,work_date='2099-02-01',lines=[dict(work_item='My own description',hours=1,result='Completed',item_code=code,item_name_snapshot='forged')])).insert()
    row=doc.lines[0];assert row.work_item=='My own description' and row.uom=='PoC Piece' and row.item_name_snapshot=='Material selection test'
    row.item_name_snapshot='spoof';doc.save();assert row.item_name_snapshot=='Material selection test'
    row.uom=frappe.db.get_value('UOM',{'name':['!=','PoC Piece']},'name');denied(lambda:doc.save());doc.reload()
    frappe.set_user('Administrator');frappe.db.set_value('Item',code,'item_name','Renamed master')
    frappe.set_user(user);doc.save();assert doc.lines[0].item_name_snapshot=='Material selection test'
    doc.lines[0].item_code='';doc.save();assert not doc.lines[0].item_name_snapshot and doc.lines[0].work_item=='My own description'
    doc.lines[0].item_code=code;doc.save()
    transition(doc.name,'submit',frappe.db.get_value(doc.doctype,doc.name,'modified'))
    doc.reload();doc.lines[0].item_code='';denied(lambda:doc.save())
    frappe.set_user('Administrator');frappe.db.set_value('Item',code,'disabled',1)
    frappe.set_user(user);assert not search_items('RPM-ROLLBACK')
    frappe.set_user('Guest');denied(lambda:search_items(''))
    print('ITEM_TEST_PASS optional link, safe search, preserve text, snapshot, units, unlink, lock, disabled, Guest')
finally:
    frappe.db.rollback();frappe.set_user('Administrator')
