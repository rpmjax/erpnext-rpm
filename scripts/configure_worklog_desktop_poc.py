"""Add a native v16 desktop entry on the isolated work-log PoC site."""
import frappe
from frappe.boot import get_bootinfo

assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
assert frappe.session.user == 'Administrator'
label = '我的工作紀錄'
role = 'RPM Work Log Pilot'
assert frappe.db.exists('Workspace', 'My Work Logs')
sidebar = frappe.get_doc('Workspace Sidebar', label) if frappe.db.exists('Workspace Sidebar', label) else frappe.new_doc('Workspace Sidebar')
sidebar.update(dict(title=label, standard=0, header_icon='clipboard'))
sidebar.set('items', [dict(type='Link', label=label, link_type='Workspace', link_to='My Work Logs')])
sidebar.save()
icon = frappe.get_doc('Desktop Icon', label) if frappe.db.exists('Desktop Icon', label) else frappe.new_doc('Desktop Icon')
icon.update(dict(label=label, standard=0, icon_type='Link', link_type='Workspace Sidebar',
                 link_to=label, icon='clipboard', bg_color='blue', hidden=0, parent_icon=None))
icon.set('roles', [dict(role=role)])
icon.save()
frappe.db.commit()
frappe.clear_cache()
pilots = frappe.get_all('Has Role', filters={'parenttype':'User', 'role':role}, pluck='parent')
assert len(pilots) == 2
try:
    for user in pilots:
        frappe.set_user(user)
        boot = get_bootinfo()
        matches = [i for i in boot.desktop_icons if i.label == label]
        assert len(matches) == 1 and not matches[0].hidden
        items = boot.workspace_sidebar_item[label.lower()]['items']
        assert items[0]['link_to'] == 'My Work Logs' and items[0]['link_type'] == 'Workspace'
        print('Pilot desktop icon and workspace destination PASS')
finally:
    frappe.set_user('Administrator')
print('DESKTOP_ENTRY_PASS')
