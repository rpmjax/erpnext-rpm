import frappe
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
users=frappe.get_all('Has Role', filters={'parenttype':'User','role':'RPM Work Log Pilot'}, pluck='parent')
from frappe.utils.safe_exec import safe_exec
script=frappe.get_doc('Server Script','RPM Work Log Daily Summary')
try:
    docs=[]
    for user in users:
        frappe.set_user(user)
        employee=frappe.db.get_value('Employee', {'user_id':user}, 'name')
        def build():
            return frappe.get_doc(dict(doctype='RPM Daily Work Log', title='Same title rules test', work_date='2099-01-01', employee=employee, department='forged', total_hours=999, lines=[dict(work_item='Test',result='Completed',hours=1.25),dict(work_item='Test 2',result='Completed',hours=0.75,record_quantity=1,quantity=0,uom='PoC Piece')]))
        a=build().insert(); b=build().insert()
        assert a.total_hours==2 and a.employee_name and a.department!='forged'
        assert a.name != b.name
        a.lines[0].hours=2.25; a.save(); assert a.total_hours==3
        frappe.local.form_dict=frappe._dict(work_date='2099-01-01',employee='forged')
        script.execute_method()
        assert frappe.response['message']['total_hours']==5, frappe.response['message']
        b.work_date='2099-01-02'; b.save()
        script.execute_method(); assert frappe.response['message']['total_hours']==3
        for label, mutation in [
            ('blank title', lambda d:setattr(d,'title','   ')),
            ('no rows', lambda d:d.set('lines',[])),
            ('zero hours',lambda d:setattr(d.lines[0],'hours',0)),
            ('negative quantity',lambda d:setattr(d.lines[0],'quantity',-1)),
            ('missing unit',lambda d:setattr(d.lines[0],'quantity',5)),
            ('zero quantity missing unit',lambda d:setattr(d.lines[0],'record_quantity',1)),
            ('too many hours',lambda d:setattr(d.lines[0],'hours',24)),
            ('bad result',lambda d:setattr(d.lines[0],'result','BAD')),
        ]:
            d=build(); mutation(d)
            try: d.insert()
            except frappe.ValidationError: pass
            else: raise AssertionError(label+' accepted')
        docs.append(a)
        print('Pilot: same-title multiple documents, totals, date move, invalid inputs PASS')
    assert not docs[0].has_permission('read')
    print('RULES_TEST_PASS')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
