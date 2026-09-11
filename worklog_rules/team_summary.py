# Dedicated read-only endpoint. Never grant broad Work Log read permissions.
if not frappe.db.exists('Has Role', {'parenttype':'User','parent':frappe.session.user,'role':'RPM Work Log Manager Pilot'}):
    frappe.throw('未授權主管查閱')
manager = frappe.db.get_value('Employee', {'user_id':frappe.session.user,'status':'Active'}, 'name')
if not manager:
    frappe.throw('帳號沒有有效主管員工關聯')
start = frappe.utils.getdate(frappe.form_dict.get('from_date') or frappe.utils.today())
end = frappe.utils.getdate(frappe.form_dict.get('to_date') or frappe.utils.today())
if frappe.utils.date_diff(end, start) < 0 or frappe.utils.date_diff(end, start) > 31:
    frappe.throw('請選擇起訖順序正確且不超過 31 天差距的範圍')
reports = frappe.get_all('Employee', filters={'reports_to':manager,'status':'Active'}, fields=['name','employee_name','department'])
ids = []
for e in reports:
    ids.append(e.name)
logs = []
if ids:
    filters = {'employee':['in',ids], 'work_date':['between',[start,end]]}
    if frappe.form_dict.get('name'):
        filters['name'] = frappe.form_dict.get('name')
    logs = frappe.get_all('RPM Daily Work Log', filters=filters, fields=['name','title','work_date','employee','total_hours'], order_by='work_date desc, name desc', limit_page_length=301)
truncated = len(logs) > 300
logs = logs[:300]
for log in logs:
    for e in reports:
        if e.name == log.employee:
            log['employee_name'] = e.employee_name
            log['department'] = e.department
    log['lines'] = frappe.get_all('RPM Work Log Line', filters={'parent':log.name,'parenttype':'RPM Daily Work Log','parentfield':'lines'}, fields=['activity_type','work_item','record_quantity','quantity','uom','result','hours','note'], order_by='idx asc', limit_page_length=0)
frappe.response['message'] = {'logs':logs,'truncated':truncated,'direct_report_count':len(ids)}
