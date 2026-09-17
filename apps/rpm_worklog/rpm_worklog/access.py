"""Explicit administrator enrollment; no automatic role grants or account creation."""
from pathlib import Path
import frappe

EMPLOYEE_ROLE = 'RPM Work Log Pilot'
MANAGER_ROLE = 'RPM Work Log Manager Pilot'
DOCTYPE = 'RPM Work Log Access'


def require_admin():
    if frappe.session.user == 'Guest' or not frappe.db.get_value('User', frappe.session.user, 'enabled'):
        frappe.throw('Not permitted', frappe.PermissionError)
    if frappe.session.user != 'Administrator' and 'System Manager' not in frappe.get_roles():
        frappe.throw('System Manager required', frappe.PermissionError)


def inspect_user(user):
    doc = frappe.get_doc('User', user)
    employees = frappe.get_all('Employee', filters={'user_id': user, 'status': 'Active'},
        fields=['name', 'employee_number', 'employee_name'], limit_page_length=2)
    reasons = []
    if user in ('Guest', 'Administrator'):
        reasons.append('系統內建帳號不開通')
    if not doc.enabled:
        reasons.append('User 未啟用')
    if doc.user_type != 'System User':
        reasons.append('User 必須為 System User')
    if len(employees) != 1:
        reasons.append('必須唯一綁定一筆 Active Employee')
    employee = employees[0] if len(employees) == 1 else None
    permissions = frappe.get_all('User Permission', filters={'user': user, 'allow': 'Employee'},
        fields=['name', 'for_value', 'apply_to_all_doctypes', 'is_default', 'hide_descendants'], limit_page_length=0)
    if employee and any(p.for_value != employee.name for p in permissions):
        reasons.append('既有 Employee User Permission 指向其他員工，請先人工核對')
    own = [p for p in permissions if employee and p.for_value == employee.name]
    adjustments = []
    if len(own) > 1:
        reasons.append('有多筆本人 Employee User Permission，請先人工核對')
    elif own:
        for field, label in [('apply_to_all_doctypes','套用至所有文件'), ('is_default','設為預設'), ('hide_descendants','不包含下屬')]:
            if not own[0].get(field):
                adjustments.append(f'{label}：未勾選 → 勾選')
    default = frappe.db.get_value('DefaultValue', {'parent': user, 'defkey': 'Employee'}, 'defvalue')
    if employee and default and default != employee.name:
        reasons.append('預設 Employee 與目前綁定不符，請先人工核對')
    roles = [r.role for r in doc.roles]
    return dict(user=user, full_name=doc.full_name, employee=employee.name if employee else None,
        employee_label=f'{employee.employee_number or "未填工號"} | {employee.employee_name}' if employee else '',
        employee_role=EMPLOYEE_ROLE in roles, manager_role=MANAGER_ROLE in roles,
        ready=bool(employee and own and default == employee.name and not reasons and not adjustments),
        reasons=reasons, adjustments=adjustments, own_permission=own[0].name if len(own) == 1 else None)


@frappe.whitelist()
def users(text=''):
    require_admin()
    text = str(text or '').strip()[:100]
    pattern = '%' + text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    rows = frappe.get_all('User', filters={'name': ['not in', ['Guest', 'Administrator']]},
        or_filters=[[field, 'like', pattern] for field in ('name', 'full_name', 'username')],
        pluck='name', order_by='name', limit_page_length=51)
    return dict(users=[inspect_user(user) for user in rows[:50]], has_more=len(rows) > 50)


def enroll_one(user, mode, normalize_own=False):
    require_admin()
    if mode not in ('employee', 'manager'):
        frappe.throw('Invalid enrollment mode')
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE', (user,))
    status = inspect_user(user)
    if status['reasons']:
        frappe.throw('；'.join(status['reasons']))
    if status['adjustments'] and not normalize_own:
        frappe.throw('需管理員確認本人權限調整：' + '；'.join(status['adjustments']))
    role = MANAGER_ROLE if mode == 'manager' else EMPLOYEE_ROLE
    if status['ready'] and status[mode + '_role']:
        return 'unchanged'
    doc = frappe.get_doc('User', user)
    doc.append_roles(role)
    doc.save(ignore_permissions=True)
    if role not in [r.role for r in doc.roles]:
        frappe.throw('角色設定未保留 Work Log 角色，請檢查 Role Profile')
    if status['adjustments']:
        permission = frappe.get_doc('User Permission', status['own_permission'])
        permission.update(dict(apply_to_all_doctypes=1, is_default=1, hide_descendants=1))
        permission.save(ignore_permissions=True)
    if not frappe.db.exists('User Permission', {'user': user, 'allow': 'Employee', 'for_value': status['employee']}):
        frappe.get_doc(dict(doctype='User Permission', user=user, allow='Employee', for_value=status['employee'],
            apply_to_all_doctypes=1, is_default=1, hide_descendants=1)).insert(ignore_permissions=True)
    frappe.defaults.set_user_default('Employee', status['employee'], user=user)
    doc.add_comment('Info', f'Work Log enrollment: {mode}; actor: {frappe.session.user}; adjustments: ' + '；'.join(status['adjustments']))
    frappe.db.after_commit.add(frappe.clear_cache)
    return 'enrolled'


@frappe.whitelist(methods=['POST'])
def enroll(users, mode='employee', normalize_own=0):
    require_admin()
    if str(normalize_own) not in ('0', '1'):
        frappe.throw('Invalid normalization confirmation')
    users = frappe.parse_json(users) if isinstance(users, str) else users
    if mode not in ('employee', 'manager') or not isinstance(users, list) or not 1 <= len(users) <= 50:
        frappe.throw('Select 1–50 users and a valid mode')
    if any(not isinstance(user, str) for user in users):
        frappe.throw('Invalid users')
    results = []
    for i, user in enumerate(dict.fromkeys(users)):
        point = f'worklog_enroll_{i}'
        frappe.db.savepoint(point)
        try:
            result = enroll_one(user, mode, normalize_own=str(normalize_own) == '1')
            results.append(dict(user=user, status=result))
        except (frappe.ValidationError, frappe.DoesNotExistError) as exc:
            frappe.db.rollback(save_point=point)
            results.append(dict(user=user, status='failed', reason=str(exc)))
    return results


def install():
    if not frappe.db.exists('DocType', DOCTYPE):
        frappe.get_doc(dict(doctype='DocType', name=DOCTYPE, module='Custom', custom=1, issingle=1,
            fields=[dict(fieldname='controls', label='Enrollment', fieldtype='HTML')],
            permissions=[dict(role='System Manager', read=1)])).insert()
    script = frappe.get_doc('Client Script', DOCTYPE) if frappe.db.exists('Client Script', DOCTYPE) else frappe.new_doc('Client Script')
    script.update(dict(name=DOCTYPE, dt=DOCTYPE, view='Form', enabled=1,
        script=(Path(__file__).parent / 'public/js/access.js').read_text(encoding='utf-8')))
    script.save()
    label = '工作紀錄開通管理'
    if not frappe.db.exists('Workspace Sidebar', label):
        frappe.get_doc(dict(doctype='Workspace Sidebar', title=label, standard=0, header_icon='users',
            items=[dict(type='Link', label=label, link_type='DocType', link_to=DOCTYPE)])).insert()
    if not frappe.db.exists('Desktop Icon', label):
        frappe.get_doc(dict(doctype='Desktop Icon', label=label, standard=0, icon_type='Link',
            link_type='Workspace Sidebar', link_to=label, icon='users', bg_color='blue', hidden=0,
            roles=[dict(role='System Manager')])).insert()
