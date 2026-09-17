"""Rollback-only enrollment tests, restricted to the local PoC."""
import frappe
from rpm_worklog import access

assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def denied(fn):
    try:
        fn()
    except frappe.PermissionError:
        return
    raise AssertionError('Expected PermissionError')


try:
    frappe.set_user('Administrator')
    employees = frappe.get_all('Employee', filters={'status': 'Active', 'user_id': ['not in', ['', 'Administrator']]},
        fields=['name', 'user_id'], limit_page_length=0)
    employees = [e for e in employees if len(frappe.get_all('Employee', filters={'user_id':e.user_id,'status':'Active'})) == 1
                 and 'System Manager' not in frappe.get_roles(e.user_id)]
    assert len(employees) >= 2
    first, second = employees[:2]
    user = first.user_id
    # Test incomplete enrollment using real schema, entirely rolled back.
    frappe.db.delete('User Permission', {'user': user, 'allow':'Employee'})
    frappe.defaults.set_user_default('Employee', first.name, user=user)
    doc = frappe.get_doc('User', user)
    doc.set('roles', [r for r in doc.roles if r.role not in (access.EMPLOYEE_ROLE, access.MANAGER_ROLE)])
    doc.save()
    old_roles = {r.role for r in doc.roles}
    admin = frappe.get_doc(dict(doctype='User', email='worklog-access-test@example.invalid',
        first_name='Access test', enabled=1, user_type='System User', send_welcome_email=0,
        roles=[dict(role='System Manager')])).insert()
    frappe.set_user(admin.name)
    assert not access.inspect_user(user)['reasons']
    result = access.enroll([user, 'nonexistent@example.invalid'], 'employee')
    assert [r['status'] for r in result] == ['enrolled', 'failed'], [(r['status'],r.get('reason')) for r in result]
    repeat = access.enroll([user], 'employee')[0]
    assert repeat['status'] == 'unchanged', (repeat, access.inspect_user(user))
    assert access.enroll([user], 'manager')[0]['status'] == 'enrolled'
    roles = {r.role for r in frappe.get_doc('User', user).roles}
    assert old_roles <= roles and {access.EMPLOYEE_ROLE, access.MANAGER_ROLE} <= roles
    assert frappe.db.count('User Permission', {'user':user,'allow':'Employee'}) == 1
    assert frappe.db.exists('Comment', {'reference_doctype':'User','reference_name':user,'owner':admin.name})
    # Role does not bypass current Reports To; this feature does not change it.
    original_manager = frappe.db.get_value('Employee', first.name, 'reports_to')
    assert access.inspect_user(user)['ready']
    frappe.get_doc(dict(doctype='User Permission',user=user,allow='Employee',for_value=second.name)).insert(ignore_permissions=True)
    assert access.enroll([user], 'employee')[0]['status'] == 'failed'
    assert frappe.db.count('User Permission', {'user':user,'allow':'Employee'}) == 2
    assert frappe.db.get_value('Employee', first.name, 'reports_to') == original_manager
    frappe.db.delete('User Permission', {'user':user, 'allow':'Employee', 'for_value':second.name})
    permission = frappe.db.get_value('User Permission', {'user':user,'allow':'Employee'}, 'name')
    frappe.db.set_value('User Permission', permission, {'is_default':0,'hide_descendants':0})
    assert len(access.inspect_user(user)['adjustments']) == 2
    assert access.enroll([user], 'employee')[0]['status'] == 'failed'
    assert access.enroll([user], 'employee', normalize_own=1)[0]['status'] == 'enrolled'
    assert access.inspect_user(user)['ready']
    assert frappe.db.count('User Permission', {'user':user,'allow':'Employee'}) == 1
    assert access.enroll([user], 'employee', normalize_own=1)[0]['status'] == 'unchanged'
    frappe.db.set_value('User',user,'enabled',0)
    assert access.enroll([user], 'employee')[0]['status'] == 'failed'
    frappe.db.set_value('User',user,'enabled',1)
    frappe.db.set_value('Employee',second.name,'user_id',user)
    assert access.enroll([user], 'employee')[0]['status'] == 'failed'
    frappe.set_user(user)
    denied(lambda: access.users())
    denied(lambda: access.enroll([user], 'manager'))
    frappe.set_user('Guest')
    denied(lambda: access.users())
    denied(lambda: access.enroll([user]))
    print('ACCESS_TEST_PASS: System Manager, batch partial results, idempotency, roles preserved, audit, conflicting permissions, disabled/duplicate employee, employee/manager/Guest denial')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
    frappe.clear_cache()
