"""Two-user native-permission pilot, isolated Docker site only.

Selection file /tmp/worklog-pilots.json is local-only and contains User IDs.
No Custom App or server script. Does not grant manager approval permissions.
"""
import json
from pathlib import Path
import frappe

assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
pilots = json.loads(Path('/tmp/worklog-pilots.json').read_text(encoding='utf-8'))
assert len(pilots) == 2
role = 'RPM Work Log Pilot'
if not frappe.db.exists('Role', role):
    frappe.get_doc(dict(doctype='Role', role_name=role, desk_access=1)).insert()
dt = frappe.get_doc('DocType', 'RPM Daily Work Log')
if not any(p.role == role for p in dt.permissions):
    dt.append('permissions', dict(role=role, read=1, write=1, create=1, if_owner=1))
dt.save()
from frappe.permissions import add_permission, update_permission_property
for master in ('UOM', 'Activity Type'):
    add_permission(master, role, 0, ptype='select')
    update_permission_property(master, role, 0, 'select', 1)
    update_permission_property(master, role, 0, 'read', 0)
for user_id in pilots:
    employees = frappe.get_all('Employee', filters={'user_id':user_id,'status':'Active'}, fields=['name','department'])
    assert len(employees)==1 and employees[0].department
    emp = employees[0]
    user = frappe.get_doc('User', user_id)
    assert 'System Manager' not in [r.role for r in user.roles]
    user.append_roles(role)
    user.default_app = 'frappe'
    user.save()
    # All applicable documents: narrows Employee lookup as well as Work Log links.
    if not frappe.db.exists('User Permission', {'user':user_id,'allow':'Employee','for_value':emp.name}):
        frappe.get_doc(dict(doctype='User Permission', user=user_id, allow='Employee',
            for_value=emp.name, apply_to_all_doctypes=1, is_default=1, hide_descendants=1)).insert()
    frappe.defaults.set_user_default('Employee',emp.name,user=user_id)
script = """
frappe.ui.form.on('RPM Daily Work Log', {
    onload(frm) {
        if (!frm.is_new() || !frappe.user_roles.includes('RPM Work Log Pilot')) return;
        frappe.db.get_value('Employee', {user_id: frappe.session.user}, ['name', 'department']).then(r => {
            if (!r.message || !r.message.name) return;
            frm.set_value('employee', r.message.name);
            frm.set_value('department', r.message.department);
            if (!frm.doc.title) frm.set_value('title', 'Work Log ' + frm.doc.work_date);
        });
    },
    refresh(frm) {
        if (frappe.user_roles.includes('RPM Work Log Pilot')) frm.set_df_property('employee', 'read_only', 1);
    }
});
"""
name='RPM Work Log Pilot Defaults'
cs=frappe.get_doc('Client Script',name) if frappe.db.exists('Client Script',name) else frappe.new_doc('Client Script')
cs.update(dict(name=name,dt='RPM Daily Work Log',view='Form',enabled=1,script=script))
cs.save()
# A standard Workspace provides a stable employee entry point.
name='My Work Logs'
if not frappe.db.exists('Workspace',name):
    frappe.get_doc(dict(doctype='Workspace', label=name,title=name,module='Custom',public=1,
        roles=[dict(role=role)],
        content=json.dumps([{'id':'worklog-heading','type':'header','data':{'text':'My Work Logs','col':12}},
                            {'id':'worklog-shortcut','type':'shortcut','data':{'shortcut_name':'My Work Logs','col':3}}]),
        shortcuts=[dict(label='My Work Logs',type='DocType',link_to='RPM Daily Work Log',doc_view='List')])).insert()
frappe.db.commit()
frappe.clear_cache()
print('PILOT_CONFIGURATION_OK users=2; owner-only role plus Employee User Permission')
