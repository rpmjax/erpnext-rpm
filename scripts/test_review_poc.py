import frappe
from rpm_worklog.review import transition, history
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
users=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent')
manager=frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Manager Pilot'},pluck='parent')[0]
def denied(fn):
    try: fn()
    except (frappe.ValidationError,frappe.PermissionError,frappe.TimestampMismatchError): return
    raise AssertionError('Expected denial')
def version(name):return frappe.db.get_value('RPM Daily Work Log',name,'modified')
try:
    frappe.set_user(users[0])
    emp=frappe.db.get_value('Employee',{'user_id':users[0]},'name')
    doc=frappe.get_doc(dict(doctype='RPM Daily Work Log',title='Review rollback test',work_date='2099-02-01',employee=emp,lines=[dict(work_item='Test',hours=1,result='Completed')])).insert()
    name=doc.name
    assert doc.review_state=='Draft'
    doc.title='Edited draft';doc.save()
    doc.review_state='Approved';denied(lambda:doc.save())
    doc.reload()
    transition(name,'submit',version(name))
    assert frappe.db.get_value(doc.doctype,name,'review_state')=='Pending Review'
    doc.reload();doc.title='Forged locked edit';denied(lambda:doc.save())
    frappe.set_user(users[1]);denied(lambda:transition(name,'approve',version(name)))
    denied(lambda:history(name))
    frappe.set_user(manager)
    denied(lambda:transition(name,'return',version(name), ' '))
    stale=version(name)
    transition(name,'return',stale,'Please clarify quantity')
    frappe.set_user(users[0]);doc.reload()
    assert doc.return_reason=='Please clarify quantity'
    doc.lines[0].note='Corrected';doc.save()
    transition(name,'submit',version(name))
    frappe.set_user(manager)
    denied(lambda:transition(name,'approve',stale))
    transition(name,'approve',version(name))
    denied(lambda:transition(name,'approve',version(name)))
    events=history(name);assert len(events)==4
    assert [e.to_state for e in events]==['Pending Review','Returned','Pending Review','Approved']
    frappe.set_user(users[0]);doc.reload();denied(lambda:doc.save())
    assert doc.name==name and doc.lines[0].note=='Corrected'
    frappe.set_user('Administrator')
    event=frappe.get_doc('RPM Work Log Review Event',frappe.db.get_value('RPM Work Log Review Event',{'work_log':name},'name'))
    event.reason='tamper';denied(lambda:event.save())
    denied(lambda:frappe.delete_doc(doc.doctype,name))
    print('REVIEW_FLOW_PASS draft edit / submit / lock / return / same-ID correction / approve / audit')
    print('REVIEW_SECURITY_PASS forged status / wrong user / stale version / double approval / immutable history')
finally:
    frappe.db.rollback();frappe.set_user('Administrator')
