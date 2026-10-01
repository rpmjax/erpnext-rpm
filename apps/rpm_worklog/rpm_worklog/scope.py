"""Shared live read scope for work-log summaries and analytics."""
import frappe
from rpm_worklog.review import employee_for

MANAGEMENT_ROLE = 'RPM Worklog Management'


def analysis_scope(scope):
    """Resolve current-session analytical read scope; never grants review/write."""
    if scope in ('Self', 'Team'):
        return log_scope(scope)
    if scope != 'Organization':
        frappe.throw('Invalid analysis scope', frappe.ValidationError)
    user = frappe.session.user
    if user == 'Guest' or not frappe.db.get_value('User', user, 'enabled'):
        frappe.throw('Not permitted', frappe.PermissionError)
    if MANAGEMENT_ROLE not in frappe.get_roles():
        frappe.throw('Not permitted', frappe.PermissionError)
    employee = employee_for(user)
    company = frappe.conf.get('rpm_worklog_company')
    if not company or not frappe.db.exists('Company', company):
        frappe.throw('Configure a valid rpm_worklog_company before organization analysis')
    if frappe.db.get_value('Employee', employee, 'company') != company:
        frappe.throw('Not permitted', frappe.PermissionError)
    return ["COALESCE(p.docstatus,0) != 2", 'e.company = %(scope_company)s'], {'scope_company': company}


def install_analysis_role():
    """Provision the capability only; never enroll users or grant DocType writes."""
    if not frappe.db.exists('Role', MANAGEMENT_ROLE):
        frappe.get_doc(dict(doctype='Role', role_name=MANAGEMENT_ROLE, desk_access=1)).insert()


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
