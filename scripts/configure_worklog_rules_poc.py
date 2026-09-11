"""Apply application-level rules on marked Docker PoC only. Existing rows retained."""
from pathlib import Path
import frappe
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
root = Path('/tmp/worklog_rules')
assert frappe.session.user == 'Administrator'
for dt_name, new_fields in [
    ('RPM Daily Work Log', [dict(fieldname='employee_name', label='Employee Name', fieldtype='Data', read_only=1, in_list_view=1), dict(fieldname='total_hours', label='Total Hours', fieldtype='Float', read_only=1, in_list_view=1)]),
    ('RPM Work Log Line', [dict(fieldname='record_quantity', label='記錄數量', fieldtype='Check', description='勾選後數量可為 0，但必須填單位；不計量時不勾选且數量、單位留空。')])
]:
    dt = frappe.get_doc('DocType', dt_name)
    for f in new_fields:
        if not any(x.fieldname == f['fieldname'] for x in dt.fields): dt.append('fields', f)
    for f in dt.fields:
        if f.fieldname == 'department': f.in_list_view = 1
    if dt_name == 'RPM Daily Work Log': dt.search_fields = 'employee_name,department,work_date,title'
    dt.save()
# Audit and backfill derived values only. Do not force-save or delete legacy records.
issues = []
for name in frappe.get_all('RPM Daily Work Log', pluck='name'):
    doc = frappe.get_doc('RPM Daily Work Log', name)
    total = sum(float(r.hours or 0) for r in doc.lines)
    if not doc.title or not doc.title.strip() or not doc.lines or total > 24: issues.append(name)
    for r in doc.lines:
        if r.hours <= 0 or r.quantity < 0 or (r.quantity and not r.uom): issues.append(name)
        if r.quantity or r.uom: frappe.db.set_value(r.doctype, r.name, 'record_quantity', 1, update_modified=False)
    emp = frappe.db.get_value('Employee', doc.employee, ['employee_name','department'], as_dict=True)
    frappe.db.set_value(doc.doctype, name, dict(total_hours=total, employee_name=emp.employee_name), update_modified=False)
for name, filename, values in [
    ('RPM Work Log Validation', 'validate.py', dict(script_type='DocType Event', reference_doctype='RPM Daily Work Log', doctype_event='Before Validate')),
    ('RPM Work Log Daily Summary', 'daily_summary.py', dict(script_type='API', api_method='rpm_worklog_daily_summary', allow_guest=0))
]:
    ss = frappe.get_doc('Server Script', name) if frappe.db.exists('Server Script', name) else frappe.new_doc('Server Script')
    ss.update(dict(name=name, script=root.joinpath(filename).read_text(encoding='utf-8-sig'), disabled=0, **values))
    ss.save()
name = 'RPM Work Log Totals'
cs = frappe.get_doc('Client Script', name) if frappe.db.exists('Client Script', name) else frappe.new_doc('Client Script')
cs.update(dict(name=name, dt='RPM Daily Work Log', view='Form', enabled=1, script=root.joinpath('form.js').read_text(encoding='utf-8-sig')))
cs.save()
frappe.db.commit()
frappe.clear_cache()
print('RULES_CONFIGURED; legacy_records_needing_review=', sorted(set(issues)))
