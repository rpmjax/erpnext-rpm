"""Optional cross-day targets; ownership is distinct from daily work entries."""
import frappe
from frappe.utils import getdate
from rpm_worklog.review import employee_for

DT = 'RPM Work Target'


def actor(user=None):
    user = user or frappe.session.user
    if user == 'Guest' or not frappe.db.get_value('User', user, 'enabled'):
        return None, set()
    try:
        return employee_for(user), set(frappe.get_roles(user))
    except frappe.PermissionError:
        return None, set()


def has_permission(doc, user=None, ptype=None, permission_type=None):
    permission_type = ptype or permission_type
    user = user or frappe.session.user
    employee, roles = actor(user)
    if not employee:
        return False
    own = doc.owner == user and doc.employee == employee and 'RPM Work Log Pilot' in roles
    if permission_type == 'create':
        return 'RPM Work Log Pilot' in roles
    if permission_type in ('read', 'select'):
        if own:
            return True
        return bool('RPM Work Log Manager Pilot' in roles and doc.employee != employee
                    and frappe.db.exists('Employee', {'name':doc.employee, 'status':'Active',
                        'reports_to':employee, 'user_id':doc.owner}))
    if permission_type in ('write',):
        return own
    return False


def permission_query(user=None):
    user = user or frappe.session.user
    employee, roles = actor(user)
    if not employee:
        return '1=0'
    esc = frappe.db.escape
    parts = []
    if 'RPM Work Log Pilot' in roles:
        parts.append(f'(`tabRPM Work Target`.owner={esc(user)} AND `tabRPM Work Target`.employee={esc(employee)})')
    if 'RPM Work Log Manager Pilot' in roles:
        parts.append(f"""EXISTS (SELECT 1 FROM `tabEmployee` e WHERE e.name=`tabRPM Work Target`.employee
            AND e.user_id=`tabRPM Work Target`.owner AND e.status='Active'
            AND e.reports_to={esc(employee)} AND e.name!={esc(employee)})""")
    return '(' + ' OR '.join(parts) + ')' if parts else '1=0'


def validate(doc, method=None):
    if doc.is_new():
        employee, roles = actor()
        if 'RPM Work Log Pilot' not in roles:
            frappe.throw('Employee work-log role required', frappe.PermissionError)
        doc.owner = frappe.session.user
        doc.employee = employee
    else:
        old = frappe.get_doc(DT, doc.name)
        if not has_permission(old, permission_type='write'):
            frappe.throw('Only the target owner may edit', frappe.PermissionError)
        if doc.owner != old.owner or doc.employee != old.employee:
            frappe.throw('Target ownership cannot be changed')
    doc.target_name = (doc.target_name or '').strip()
    if not doc.target_name:
        frappe.throw('Target name is required')
    if doc.status not in ('Open', 'Closed', 'Archived'):
        frappe.throw('Invalid target status')
    if doc.start_date and doc.due_date and getdate(doc.start_date) > getdate(doc.due_date):
        frappe.throw('Due date must not precede start date')


def prevent_delete(doc, method=None):
    frappe.throw('Archive the target instead of deleting it, to preserve work-log history')


def validate_entries(doc, method=None):
    old = doc.get_doc_before_save()
    if old is None and not doc.is_new():
        old = frappe.get_doc(doc.doctype, doc.name)
    previous = {r.name:r.get('work_target') for r in old.lines} if old else {}
    for row in doc.lines or []:
        if not row.get('work_target'):
            continue
        target = frappe.get_doc(DT, row.work_target)
        if target.owner != doc.owner or target.employee != doc.employee:
            frappe.throw('Work entries may only link their owner’s targets', frappe.PermissionError)
        if target.status != 'Open' and previous.get(row.name) != row.work_target:
            frappe.throw('Choose an open target; closed or archived links are retained only on existing entries')


def install():
    from pathlib import Path
    if not frappe.db.exists('DocType', DT):
        fields = [
            dict(fieldname='target_name',label='目標名稱',fieldtype='Data',reqd=1,in_list_view=1),
            dict(fieldname='employee',label='Employee',fieldtype='Link',options='Employee',read_only=1,hidden=1,ignore_user_permissions=1),
            dict(fieldname='status',label='狀態',fieldtype='Select',options='Open\nClosed\nArchived',default='Open',reqd=1,in_list_view=1),
            dict(fieldname='manufacturing_order_no',label='製令單號（選填）',fieldtype='Data'),
            dict(fieldname='start_date',label='開始日期（選填）',fieldtype='Date'),
            dict(fieldname='due_date',label='預計完成日期（選填）',fieldtype='Date',in_list_view=1),
            dict(fieldname='description',label='說明',fieldtype='Small Text'),
        ]
        frappe.get_doc(dict(doctype='DocType',name=DT,module='Custom',custom=1,
            autoname='format:RWT-{YYYY}-{#####}',title_field='target_name',search_fields='target_name,manufacturing_order_no',
            track_changes=1,fields=fields,permissions=[
                dict(role='RPM Work Log Pilot',read=1,write=1,create=1,select=1),
                dict(role='RPM Work Log Manager Pilot',read=1,select=1,write=0,create=0,delete=0),
            ])).insert()
    definition = frappe.get_doc('DocType', DT)
    for perm in definition.permissions:
        for action in ('delete','share','export','import','submit','cancel','amend'):
            perm.set(action, 0)
        if perm.role == 'RPM Work Log Manager Pilot':
            perm.write = perm.create = 0
    definition.save()
    line = frappe.get_doc('DocType', 'RPM Work Log Line')
    if not line.get('fields', {'fieldname':'work_target'}):
        line.append('fields', dict(fieldname='work_target',label='跨日工作目標（選填）',fieldtype='Link',
            options=DT,description='臨時或例行工作可以留空；需要跨日追蹤時再建立目標。'))
        line.save()
    script_name = 'RPM Optional Work Target'
    script = frappe.get_doc('Client Script',script_name) if frappe.db.exists('Client Script',script_name) else frappe.new_doc('Client Script')
    script.update(dict(name=script_name,dt='RPM Daily Work Log',view='Form',enabled=1,
        script=(Path(__file__).parent / 'public/js/targets.js').read_text(encoding='utf-8')))
    script.save()
    for sidebar in ('我的工作紀錄', '直屬員工工作紀錄'):
        if frappe.db.exists('Workspace Sidebar', sidebar):
            doc = frappe.get_doc('Workspace Sidebar', sidebar)
            if not any(r.link_to == DT for r in doc.items):
                doc.append('items',dict(type='Link',label='跨日工作目標',link_type='DocType',link_to=DT))
                # Preserve existing navigation (including legacy translated links).
                # Only the newly added link is owned here and its DocType exists above.
                doc.flags.ignore_links = True
                doc.save()
