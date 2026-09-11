# Authenticated endpoint, always scoped to the caller's linked Employee.
employee = frappe.db.get_value('Employee', {'user_id': frappe.session.user, 'status': 'Active'}, 'name')
if not employee:
    frappe.throw('目前帳號沒有有效的員工關聯')
date = frappe.utils.getdate(frappe.form_dict.get('work_date'))
rows = frappe.get_list('RPM Daily Work Log', filters={'employee': employee, 'work_date': date}, fields=['name', 'total_hours'], limit_page_length=0)
total = 0
for row in rows:
    total = total + frappe.utils.flt(row.total_hours)
frappe.response['message'] = {'total_hours': total, 'record_count': len(rows)}
