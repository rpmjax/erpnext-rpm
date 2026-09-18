"""Optional same-day time range; never a running timer."""
from datetime import time, timedelta
import re
import frappe


def seconds(value):
    if value is None or value == '':
        return None
    if isinstance(value, timedelta):
        result = value.total_seconds()
    elif isinstance(value, time):
        result = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
    else:
        match = re.fullmatch(r'(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?', str(value))
        if not match:
            frappe.throw('時間格式須為 HH:mm 或 HH:mm:ss')
        hour, minute, second = [int(v or 0) for v in match.groups()[:3]]
        if hour > 23 or minute > 59 or second > 59:
            frappe.throw('請填寫有效時間（00:00 至 23:59:59）')
        result = hour * 3600 + minute * 60 + second + float('0.' + (match[4] or '0'))
    if not 0 <= result < 86400:
        frappe.throw('請填寫有效的同日時間')
    return result


def apply(row):
    start, end = seconds(row.get('start_time')), seconds(row.get('end_time'))
    if start is None or end is None:
        return  # Preserve manual/existing hours when either endpoint is absent.
    if end <= start:
        frappe.throw('結束時間須晚於開始時間；跨午夜請拆成不同日期的工作列')
    row.hours = frappe.utils.flt((end - start) / 3600, row.precision('hours'))
    if row.hours <= 0:
        frappe.throw('時間區間過短，無法以目前工時精度記錄')


def install():
    from pathlib import Path
    line = frappe.get_doc('DocType', 'RPM Work Log Line')
    for name, label in [('start_time','開始時間（選填）'),('end_time','結束時間（選填）')]:
        if not line.get('fields', {'fieldname':name}):
            line.append('fields',dict(fieldname=name,label=label,fieldtype='Time',
                description='兩者完整時自動換算工時；不完整時保留手填工時。不計時、不扣午休、不支援跨午夜。'))
    timed = [line.get('fields', {'fieldname':name})[0] for name in ('start_time','end_time')]
    for field in timed:
        line.fields.remove(field)
    index = next(i for i,f in enumerate(line.fields) if f.fieldname == 'hours')
    line.fields[index:index] = timed
    for index, field in enumerate(line.fields, 1):
        field.idx = index
    line.save()
    name = 'RPM Optional Entry Time'
    script = frappe.get_doc('Client Script',name) if frappe.db.exists('Client Script',name) else frappe.new_doc('Client Script')
    script.update(dict(name=name,dt='RPM Daily Work Log',view='Form',enabled=1,
        script=(Path(__file__).parent/'public/js/entry_time.js').read_text(encoding='utf-8')))
    script.save()
