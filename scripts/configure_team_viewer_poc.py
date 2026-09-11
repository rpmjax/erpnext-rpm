from pathlib import Path
import json
import frappe
assert frappe.local.site=='frontend' and frappe.conf.get('rpm_worklog_model_poc')
assert frappe.session.user=='Administrator'
role='RPM Work Log Manager Pilot'
if not frappe.db.exists('Role',role): frappe.get_doc(dict(doctype='Role',role_name=role,desk_access=1)).insert()
manager_users=set()
for user in frappe.get_all('Has Role',filters={'parenttype':'User','role':'RPM Work Log Pilot'},pluck='parent'):
    manager=frappe.db.get_value('Employee',{'user_id':user},'reports_to')
    uid=frappe.db.get_value('Employee',manager,'user_id') if manager else None
    assert uid and frappe.db.get_value('User',uid,'enabled')
    manager_users.add(uid)
for uid in manager_users:
    u=frappe.get_doc('User',uid)
    assert 'System Manager' not in [r.role for r in u.roles]
    u.append_roles(role); u.save()
name='RPM Team Work Log Viewer'
if not frappe.db.exists('DocType',name):
    frappe.get_doc(dict(doctype='DocType',name=name,module='Custom',custom=1,issingle=1,
        fields=[dict(fieldname='from_date',label='From Date',fieldtype='Date'),dict(fieldname='to_date',label='To Date',fieldtype='Date'),dict(fieldname='results',label='Results',fieldtype='HTML')],
        permissions=[dict(role=role,read=1),dict(role='System Manager',read=1)])).insert()
root=Path('/tmp/worklog_rules')
for dt,n,values in [
 ('Server Script','RPM Team Work Logs',dict(script_type='API',api_method='rpm_team_worklogs',allow_guest=0,disabled=0,script=root.joinpath('team_summary.py').read_text(encoding='utf-8-sig'))),
 ('Client Script','RPM Team Viewer',dict(dt=name,view='Form',enabled=1,script=root.joinpath('team_viewer.js').read_text(encoding='utf-8-sig')))]:
    d=frappe.get_doc(dt,n) if frappe.db.exists(dt,n) else frappe.new_doc(dt)
    d.update(dict(name=n,**values));d.save()
label='直屬員工工作紀錄'
sidebar=frappe.get_doc('Workspace Sidebar',label) if frappe.db.exists('Workspace Sidebar',label) else frappe.new_doc('Workspace Sidebar')
sidebar.update(dict(title=label,standard=0,header_icon='clipboard'))
sidebar.set('items',[dict(type='Link',label=label,link_type='DocType',link_to=name)])
sidebar.save()
icon=frappe.get_doc('Desktop Icon',label) if frappe.db.exists('Desktop Icon',label) else frappe.new_doc('Desktop Icon')
icon.update(dict(label=label,standard=0,icon_type='Link',link_type='Workspace Sidebar',link_to=label,icon='clipboard',bg_color='blue',hidden=0))
icon.set('roles',[dict(role=role)]);icon.save()
frappe.db.commit();frappe.clear_cache()
print('TEAM_VIEWER_CONFIGURED managers=',len(manager_users))
