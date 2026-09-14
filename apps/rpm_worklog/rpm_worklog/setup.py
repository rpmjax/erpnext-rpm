from pathlib import Path
import frappe

def install():
    assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
    line=frappe.get_doc('DocType','RPM Work Log Line')
    fields=[
        dict(fieldname='search_item',label='Search Item',fieldtype='Button'),
        dict(fieldname='item_code',label='Linked Item',fieldtype='Link',options='Item',read_only=1,in_list_view=1),
        dict(fieldname='item_name_snapshot',label='Item Name at Selection',fieldtype='Data',read_only=1),
        dict(fieldname='clear_item',label='Remove Item Link',fieldtype='Button'),
        dict(fieldname='item_stock_uom',label='Item Stock UOM',fieldtype='Link',options='UOM',read_only=1),
        dict(fieldname='item_conversion_factor',label='Item UOM Conversion Factor',fieldtype='Float',read_only=1),
    ]
    for field in fields:
        if not any(f.fieldname==field['fieldname'] for f in line.fields):line.append('fields',field)
    for f in line.fields:
        if f.fieldname in ('uom','item_stock_uom','item_conversion_factor'):
            f.hidden = 1
            f.in_list_view = 0
            f.reqd = 0
        if f.fieldname == 'record_quantity':
            f.hidden = 1
            f.in_list_view = 0
            f.read_only = 1
            f.description = '勾選表示記錄數量，數量可為 0；目前暫不使用單位。'
    line.save()
    dt=frappe.get_doc('DocType','RPM Daily Work Log')
    for field in [dict(fieldname='review_state',label='Review Status',fieldtype='Select',options='Draft\nPending Review\nReturned\nApproved',default='Draft',read_only=1,in_list_view=1),dict(fieldname='return_reason',label='Return Reason',fieldtype='Small Text',read_only=1)]:
        if not any(f.fieldname==field['fieldname'] for f in dt.fields):dt.append('fields',field)
    hint = next((f for f in dt.fields if f.fieldname == 'work_entry_help'), None)
    if hint is None:
        hint = dt.append('fields', dict(fieldname='work_entry_help', label='Work Entry Help', fieldtype='HTML'))
    hint.options = '<div class="alert alert-info" role="note"><strong>填寫與物料搜尋</strong><br>可直接在下方表格填寫工作內容。需要挑選物料時：<strong>點該列最右側的鉛筆 ✎ → 展開明細 → 搜尋物料（Search Item）</strong>。<br>若看不到鉛筆，請將表格向右捲動；沒有工作列時，先按「添加行」。物料為選填，不搜尋也能記錄工作。</div>'
    dt.fields.remove(hint)
    dt.fields.insert(next(i for i, f in enumerate(dt.fields) if f.fieldname == 'lines'), hint)
    for index, field in enumerate(dt.fields, 1): field.idx = index
    dt.save()
    frappe.db.sql("UPDATE `tabRPM Daily Work Log` SET review_state='Draft' WHERE review_state IS NULL OR review_state=''")
    name='RPM Work Log Review Event'
    if not frappe.db.exists('DocType',name):
        fields=[dict(fieldname=n,label=label,fieldtype=kind,**opts) for n,label,kind,opts in [
            ('work_log','Work Log','Link',{'options':'RPM Daily Work Log'}),
            ('from_state','From State','Data',{}),('to_state','To State','Data',{}),('action','Action','Data',{}),
            ('actor','Actor','Link',{'options':'User'}),('event_time','Event Time','Datetime',{}),('reason','Reason','Small Text',{})]]
        frappe.get_doc(dict(doctype='DocType',name=name,module='Custom',custom=1,autoname='hash',fields=fields,permissions=[dict(role='System Manager',read=1)])).insert()
    # App hook replaces the prototype event validation; no duplicate execution.
    frappe.db.set_value('Server Script','RPM Work Log Validation','disabled',1)
    root=Path(__file__).parent / 'public' / 'js'
    for name,dt,source in [('RPM Item Picker','RPM Daily Work Log','item_picker.js'),('RPM Employee Review','RPM Daily Work Log','employee_review.js'),('RPM Team Viewer','RPM Team Work Log Viewer','team_review.js')]:
        d=frappe.get_doc('Client Script',name) if frappe.db.exists('Client Script',name) else frappe.new_doc('Client Script')
        d.update(dict(name=name,dt=dt,view='Form',enabled=1,script=root.joinpath(source).read_text(encoding='utf-8-sig')));d.save()
    d=frappe.get_doc('Server Script','RPM Team Work Logs')
    d.script=d.script.replace("'employee','total_hours']", "'employee','total_hours','review_state','modified']")
    d.script=d.script.replace("'hours','note']", "'hours','note','item_code','item_name_snapshot']")
    d.save()
    frappe.clear_cache()
