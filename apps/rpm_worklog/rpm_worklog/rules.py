import frappe
from rpm_worklog.items import validate_items

def validate_data(doc):
    # Runs as a native Before Validate Server Script.
    if not doc.title or not doc.title.strip():
        frappe.throw('Title 不可空白')
    if not doc.lines:
        frappe.throw('至少填寫一列工作')
    emp = frappe.db.get_value('Employee', doc.employee, ['user_id', 'department', 'employee_name'], as_dict=True)
    if not emp:
        frappe.throw('請選擇有效員工')
    if frappe.session.user != 'Administrator' and emp.user_id != frappe.session.user:
        frappe.throw('只能填寫本人的工作紀錄')
    doc.department = emp.department
    doc.employee_name = emp.employee_name
    validate_items(doc)
    total = 0
    for row in doc.lines:
        if row.result not in ['In Progress', 'Completed', 'Blocked']:
            frappe.throw('請選擇有效的工作結果')
        hours = frappe.utils.flt(row.hours)
        if not (hours > 0 and hours <= 24):
            frappe.throw('每列工時必須大於 0 且不超過 24 小時')
        qty = frappe.utils.flt(row.quantity)
        if not (qty >= 0 and qty < float('inf')):
            frappe.throw('數量必須為有效的非負數')
        total = total + hours
    if total > 24:
        frappe.throw('單張總工時不可超過 24 小時')
    doc.total_hours = total
