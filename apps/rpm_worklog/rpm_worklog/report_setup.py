from pathlib import Path
import frappe


def install():
    name = 'RPM Work Log Report'
    if not frappe.db.exists('DocType', name):
        fields = [
            dict(fieldname='report_title', label='Report Title', fieldtype='Data', reqd=1),
            dict(fieldname='enabled', label='Enabled', fieldtype='Check', default='1'),
            dict(fieldname='grain', label='Data Grain', fieldtype='Select', options='Log\nEntry', default='Log', reqd=1, description='Log: one whole work log. Entry: one work entry row.'),
            dict(fieldname='group_field', label='Group Field', fieldtype='Select', options='work_date\nemployee\ndepartment\nreview_state\nactivity_type\nitem_code\nresult', reqd=1),
            dict(fieldname='operation', label='Operation', fieldtype='Select', options='Sum\nCount\nAverage', default='Sum', reqd=1),
            dict(fieldname='measure_field', label='Measure Field', fieldtype='Select', options='\ntotal_hours\nhours', description='Log uses total_hours; Entry uses hours. Leave empty for Count.'),
            dict(fieldname='sort_order', label='Sort Order', fieldtype='Select', options='Group Ascending\nValue Descending', default='Group Ascending', reqd=1),
            dict(fieldname='chart_type', label='Chart Type', fieldtype='Select', options='bar\nline\npie', default='bar', reqd=1),
            dict(fieldname='default_state', label='Default Review Status', fieldtype='Select', options='All\nDraft\nPending Review\nReturned\nApproved', default='All', reqd=1),
        ]
        frappe.get_doc(dict(doctype='DocType', name=name, module='Custom', custom=1,
            autoname='hash', title_field='report_title', fields=fields,
            permissions=[dict(role='System Manager', read=1, write=1, create=1, delete=1)])).insert()
    viewer = 'RPM Work Log Analytics'
    if not frappe.db.exists('DocType', viewer):
        frappe.get_doc(dict(doctype='DocType', name=viewer, module='Custom', custom=1, issingle=1,
            fields=[dict(fieldname='results', label='Results', fieldtype='HTML')],
            permissions=[dict(role=role, read=1) for role in ['System Manager', 'RPM Work Log Pilot', 'RPM Work Log Manager Pilot']])).insert()
    for title, group, op, measure, chart in [
        ('Daily Hours', 'work_date', 'Sum', 'total_hours', 'line'),
        ('Hours by Employee', 'employee', 'Sum', 'total_hours', 'bar'),
        ('Review Status Distribution', 'review_state', 'Count', '', 'pie')]:
        # Stable IDs preserve administrator edits, including renamed titles.
        key = 'rpm-' + group
        if not frappe.db.exists(name, key):
            frappe.get_doc(dict(doctype=name, name=key, report_title=title, enabled=1, grain='Log',
                group_field=group, operation=op, measure_field=measure, sort_order='Group Ascending',
                chart_type=chart, default_state='All')).insert(set_name=key)
    script_name = 'RPM Work Log Analytics'
    script = frappe.get_doc('Client Script', script_name) if frappe.db.exists('Client Script', script_name) else frappe.new_doc('Client Script')
    script.update(dict(name=script_name, dt=viewer, view='Form', enabled=1,
        script=(Path(__file__).parent / 'public/js/analytics.js').read_text(encoding='utf-8-sig')))
    script.save()
