"""Versioned bootstrap for explicitly managed standalone sites. No personal data."""
import json
import frappe


def bootstrap():
    if not frappe.conf.get('rpm_worklog_managed'):
        frappe.throw('This site must explicitly enable rpm_worklog_managed before installation')
    for role in ('RPM Work Log Pilot', 'RPM Work Log Manager Pilot'):
        if not frappe.db.exists('Role', role):
            frappe.get_doc(dict(doctype='Role', role_name=role, desk_access=1)).insert()
    def f(name, label, kind, **kw):
        return dict(fieldname=name, label=label, fieldtype=kind, **kw)
    definitions = [
        dict(name='RPM Work Log Line', istable=1, editable_grid=1, fields=[
            f('activity_type','Activity Type','Link',options='Activity Type',in_list_view=1),
            f('work_item','Work Item','Data',hidden=1),
            f('quantity','Completed Quantity','Float',in_list_view=1),
            f('uom','UOM','Link',options='UOM',hidden=1),
            f('result','Result','Select',options='In Progress\nCompleted\nBlocked',reqd=1,in_list_view=1),
            f('hours','Hours','Float',reqd=1,in_list_view=1),
            f('note','Note','Small Text'), f('record_quantity','Record Quantity','Check',hidden=1)]),
        dict(name='RPM Daily Work Log', autoname='format:RWL-{YYYY}-{#####}', title_field='title', track_changes=1,
            search_fields='employee_name,department,work_date,title', fields=[
                f('title','Title','Data',reqd=1), f('work_date','Work Date','Date',default='Today',reqd=1,in_list_view=1),
                f('employee','Employee','Link',options='Employee',reqd=1),
                f('employee_name','Employee Name','Data',read_only=1,in_list_view=1),
                f('department','Department','Link',options='Department',read_only=1,in_list_view=1),
                f('total_hours','Total Hours','Float',read_only=1,in_list_view=1),
                f('lines','Work Entries','Table',options='RPM Work Log Line',reqd=1)],
            permissions=[dict(role='System Manager',read=1,write=1,create=1),dict(role='RPM Work Log Pilot',read=1,write=1,create=1,if_owner=1)]),
        dict(name='RPM Team Work Log Viewer',issingle=1, fields=[
            f('from_date','From Date','Date'),f('to_date','To Date','Date'),f('results','Results','HTML')],
            permissions=[dict(role='System Manager',read=1),dict(role='RPM Work Log Manager Pilot',read=1)])]
    for definition in definitions:
        if not frappe.db.exists('DocType',definition['name']):
            frappe.get_doc(dict(doctype='DocType',module='Custom',custom=1,**definition)).insert()
    from frappe.permissions import add_permission
    # Explicit User Permission below limits Employee selection to the account's Employee.
    for master in ('Employee','Activity Type'):
        if not frappe.db.exists('Custom DocPerm',{'parent':master,'role':'RPM Work Log Pilot','select':1}):
            add_permission(master,'RPM Work Log Pilot',0,ptype='select')


def install_navigation():
    for label, target, role, color in [
        ('我的工作紀錄','RPM Daily Work Log','RPM Work Log Pilot','blue'),
        ('直屬員工工作紀錄','RPM Team Work Log Viewer','RPM Work Log Manager Pilot','blue')]:
        if not frappe.db.exists('Workspace Sidebar',label):
            frappe.get_doc(dict(doctype='Workspace Sidebar',title=label,standard=0,header_icon='clipboard',
                items=[dict(type='Link',label=label,link_type='DocType',link_to=target),
                       dict(type='Link',label='工作紀錄報表',link_type='DocType',link_to='RPM Work Log Analytics')])).insert()
        sidebar = frappe.get_doc('Workspace Sidebar', label)
        legacy = {'My Work Logs', 'Team Work Logs'}
        remaining = [item for item in sidebar.items if item.link_to not in legacy | {target}]
        sidebar.set('items', [])
        sidebar.append('items', dict(type='Link', label=label, link_type='DocType', link_to=target))
        for item in remaining:
            sidebar.append('items', item)
        if not any(item.link_to == 'RPM Work Log Analytics' for item in sidebar.items):
            sidebar.append('items', dict(type='Link', label='工作紀錄報表', link_type='DocType', link_to='RPM Work Log Analytics'))
        sidebar.save()
        if not frappe.db.exists('Desktop Icon',label):
            frappe.get_doc(dict(doctype='Desktop Icon',label=label,standard=0,icon_type='Link',
                link_type='Workspace Sidebar',link_to=label,icon='clipboard',bg_color=color,hidden=0,
                icon_image='/assets/rpm_worklog/images/team-worklogs-yellow.svg' if role == 'RPM Work Log Manager Pilot' else None,
                roles=[dict(role=role)])).insert()


def enroll(user, manager=False):
    """Local CLI wrapper sharing the UI enrollment checks."""
    if frappe.session.user != 'Administrator':
        frappe.throw('Administrator required', frappe.PermissionError)
    from rpm_worklog.access import enroll_one
    return enroll_one(user, 'manager' if manager else 'employee')
