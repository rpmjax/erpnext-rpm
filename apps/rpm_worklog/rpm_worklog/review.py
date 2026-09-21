from contextvars import ContextVar
import frappe
from frappe import _
from frappe.utils import get_datetime
from rpm_worklog.rules import validate_data

_EVENT_WRITE = ContextVar('rpm_review_event_write', default=False)
DT = 'RPM Daily Work Log'

def lock(name):
    rows = frappe.db.sql('SELECT name, modified, review_state, return_reason FROM `tabRPM Daily Work Log` WHERE name=%s FOR UPDATE', (name,), as_dict=True)
    if not rows:
        frappe.throw(_('Work log not found'))
    return rows[0]

def validate(doc, method=None):
    if doc.is_new():
        if doc.review_state not in (None, '', 'Draft') or doc.return_reason:
            frappe.throw(_('Use the review actions to change status'))
        doc.review_state = 'Draft'
    else:
        old = lock(doc.name)
        if get_datetime(old.modified) != get_datetime(doc._original_modified):
            frappe.throw(_('Record changed; reload before continuing'), frappe.TimestampMismatchError)
        if (old.review_state or 'Draft') in ('Pending Review', 'Approved'):
            frappe.throw(_('This work log is locked'))
        if (doc.review_state or 'Draft') != (old.review_state or 'Draft') or (doc.return_reason or '') != (old.return_reason or ''):
            frappe.throw(_('Use the review actions to change status'))
    validate_data(doc)

def prevent_delete(doc, method=None):
    if not doc.is_new():
        state = lock(doc.name).review_state
        if state not in (None, '', 'Draft') or frappe.db.exists('RPM Work Log Review Event', {'work_log':doc.name}):
            frappe.throw(_('Reviewed work logs cannot be deleted'))

def protect_event(doc, method=None):
    if not _EVENT_WRITE.get() or not doc.is_new():
        frappe.throw(_('Review history is immutable'))

def employee_for(user):
    rows = frappe.get_all('Employee', filters={'user_id':user,'status':'Active'}, fields=['name'], limit_page_length=2)
    if len(rows) != 1:
        frappe.throw(_('A unique active Employee is required'), frappe.PermissionError)
    return rows[0].name

def is_manager(doc):
    if 'RPM Work Log Manager Pilot' not in frappe.get_roles():
        return False
    manager = employee_for(frappe.session.user)
    employee = frappe.db.get_value('Employee', doc.employee, ['reports_to','status'], as_dict=True)
    return bool(employee and employee.status == 'Active' and employee.reports_to == manager and doc.employee != manager)

@frappe.whitelist(methods=['POST'])
def transition(name, action, expected_modified, reason=None):
    old = lock(name)
    doc = frappe.get_doc(DT, name)
    if get_datetime(old.modified) != get_datetime(expected_modified):
        frappe.throw(_('Record changed; reload before continuing'), frappe.TimestampMismatchError)
    state = old.review_state or 'Draft'
    manager_user = None
    if action == 'submit':
        doc.check_permission('write')
        if doc.employee != employee_for(frappe.session.user) or state not in ('Draft','Returned'):
            frappe.throw(_('Not allowed to submit this work log'), frappe.PermissionError)
        manager = frappe.db.get_value('Employee', doc.employee, 'reports_to')
        manager_user = frappe.db.get_value('Employee', manager, 'user_id') if manager else None
        if not manager_user or manager == doc.employee or frappe.db.get_value('Employee', manager, 'status') != 'Active' or not frappe.db.get_value('User', manager_user, 'enabled') or 'RPM Work Log Manager Pilot' not in frappe.get_roles(manager_user):
            frappe.throw(_('No enabled reviewer is configured'))
        validate_data(doc)
        target = 'Pending Review'
    elif action in ('approve','return'):
        if not is_manager(doc) or state != 'Pending Review':
            frappe.throw(_('Not allowed to review this work log'), frappe.PermissionError)
        if action == 'return' and not (reason or '').strip():
            frappe.throw(_('A return reason is required'))
        target = 'Approved' if action == 'approve' else 'Returned'
    else:
        frappe.throw(_('Unknown review action'))
    reason = (reason or '').strip() if action == 'return' else ''
    if len(reason) > 2000:
        frappe.throw(_('Return reason is too long'))
    # Only state fields change here; content is never accepted by this endpoint.
    frappe.db.set_value(DT, name, {'review_state':target,'return_reason':reason})
    token = _EVENT_WRITE.set(True)
    try:
        event = frappe.get_doc(dict(doctype='RPM Work Log Review Event', work_log=name,
            from_state=state,to_state=target,action=action,actor=frappe.session.user,
            event_time=frappe.utils.now_datetime(),reason=reason)).insert(ignore_permissions=True)
    finally:
        _EVENT_WRITE.reset(token)
    from rpm_worklog.notifications import notify_review
    notify_review(doc, event, manager_user)
    return {'name':name,'review_state':target}

@frappe.whitelist()
def history(name):
    doc = frappe.get_doc(DT,name)
    if not doc.has_permission('read') and not is_manager(doc):
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    return frappe.get_all('RPM Work Log Review Event',filters={'work_log':name},fields=['from_state','to_state','actor','event_time','reason'],order_by='creation asc',limit_page_length=0)

@frappe.whitelist(methods=['POST'])
def bulk_submit(records):
    records = frappe.parse_json(records)
    if not isinstance(records, list) or not 1 <= len(records) <= 50:
        frappe.throw(_('Select between 1 and 50 work logs'))
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row.get('modified'):
            frappe.throw(_('Invalid selection; refresh the list'))
    results = []
    seen = set()
    for index, row in enumerate(sorted(records, key=lambda r: r['name'])):
        name = row['name']
        if name in seen:
            results.append(dict(name=name,status='skipped',message=_('Duplicate selection')))
            continue
        seen.add(name)
        point = 'rpm_bulk_' + str(index)
        frappe.db.savepoint(point)
        try:
            if not frappe.db.exists(DT, name):
                frappe.throw(_('Not permitted or record unavailable'), frappe.PermissionError)
            old = lock(name)
            doc = frappe.get_doc(DT, name)
            if not doc.has_permission('write') or doc.employee != employee_for(frappe.session.user):
                frappe.throw(_('Not permitted or record unavailable'), frappe.PermissionError)
            if (old.review_state or 'Draft') not in ('Draft','Returned'):
                results.append(dict(name=name,status='skipped',message=_('Already pending or approved')))
                continue
            transition(name,'submit',row['modified'])
            results.append(dict(name=name,status='success',message=_('Sent for review')))
        except (frappe.PermissionError, frappe.ValidationError, frappe.TimestampMismatchError) as exc:
            frappe.db.rollback(save_point=point)
            message = _('Not permitted or record unavailable') if isinstance(exc,frappe.PermissionError) else str(exc)
            results.append(dict(name=name,status='failed',message=message))
    # Successful items commit with the request; each expected failure rolls back to its savepoint.
    return {'results':results, 'counts':{status:sum(r['status']==status for r in results) for status in ('success','skipped','failed')}}
