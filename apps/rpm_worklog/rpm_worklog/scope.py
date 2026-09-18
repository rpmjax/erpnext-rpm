"""Shared live read scope for work-log summaries and analytics."""
import frappe
from rpm_worklog.review import employee_for


def scopes():
    if frappe.session.user == 'Guest' or not frappe.db.get_value('User', frappe.session.user, 'enabled'):
        frappe.throw('Not permitted', frappe.PermissionError)
    employee_for(frappe.session.user)
    roles = frappe.get_roles()
    allowed = [scope for scope, role in [('Self','RPM Work Log Pilot'),('Team','RPM Work Log Manager Pilot')] if role in roles]
    if not allowed:
        frappe.throw('Not permitted', frappe.PermissionError)
    return allowed


def employee_filters(scope):
    if scope not in scopes():
        frappe.throw('Not permitted', frappe.PermissionError)
    me = employee_for(frappe.session.user)
    return {'status':'Active', **({'name':me} if scope == 'Self' else {'reports_to':me,'name':['!=',me]})}


def log_scope(scope):
    """SQL predicate for aliases p (log), e (employee); parameters never client SQL."""
    employee_filters(scope)
    me = employee_for(frappe.session.user)
    where = ["COALESCE(p.docstatus,0) != 2"]
    where += ['p.employee = %(scope_me)s', 'p.owner = %(scope_user)s'] if scope == 'Self' else [
        'e.reports_to = %(scope_me)s', "e.status = 'Active'", 'e.name != %(scope_me)s']
    return where, {'scope_me':me,'scope_user':frappe.session.user}
