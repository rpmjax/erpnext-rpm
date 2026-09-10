"""Exercise server permissions as two pilot users; test data only on marked site."""
import json
from pathlib import Path
import frappe

assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
users=json.loads(Path('/tmp/worklog-pilots.json').read_text())
employees=[frappe.db.get_value('Employee',{'user_id':u},'name') for u in users]
docs=[]
results=[]
try:
    for i,u in enumerate(users):
        frappe.set_user(u)
        doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Employee isolation PoC',
            work_date='2026-09-10',employee=employees[i],lines=[dict(activity_type='PoC Assembly',
            work_item='Assembly PoC',quantity=5,uom='PoC Piece',result='Completed',hours=1,note='Permission test')]))
        doc.insert()
        doc.check_permission('read')
        doc.lines[0].note='Saved and reopened as employee'
        doc.save()
        doc.reload()
        assert doc.lines[0].quantity==5 and doc.lines[0].hours==1
        docs.append(doc.name)
        results.append('own create/read/write PASS')
    for i,u in enumerate(users):
        frappe.set_user(u)
        foreign=frappe.get_doc('RPM Daily Work Log',docs[1-i])
        assert not foreign.has_permission('read')
        assert not foreign.has_permission('write')
        listed=[r.name for r in frappe.get_list('RPM Daily Work Log')]
        assert docs[i] in listed and docs[1-i] not in listed
        results.append('foreign read/write/list denied PASS')
        forged=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Must reject',work_date='2026-09-10',
            employee=employees[1-i],lines=[dict(work_item='Forbidden',hours=1,result='Completed')]))
        try:
            forged.insert()
        except frappe.PermissionError:
            results.append('foreign Employee create denied PASS')
        else:
            raise AssertionError('SECURITY: foreign Employee insert accepted')
    frappe.db.commit()
    Path('/tmp/worklog-pilot-test.json').write_text(json.dumps(dict(users=users,docs=docs,results=results)))
    print('\n'.join(results))
    print('PILOT_SERVER_TEST_PASS')
finally:
    frappe.set_user('Administrator')
