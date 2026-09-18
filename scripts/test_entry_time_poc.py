"""Rollback-only optional time range and persisted-hour checks."""
from datetime import timedelta
import frappe
from rpm_worklog import entry_time, review
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')


def denied(fn):
    try:
        fn()
    except (frappe.ValidationError, frappe.PermissionError):
        return
    raise AssertionError('Expected rejection')


def make(**values):
    row = dict(work_item='time test',result='In Progress',hours=2)
    row.update(values)
    return frappe.get_doc(dict(doctype='RPM Daily Work Log',title='time test',
        employee=review.employee_for(frappe.session.user),work_date='2090-01-01',lines=[row])).insert()


try:
    frappe.set_user('j250301@outlook.com')
    plain = make()
    assert plain.lines[0].hours == 2 and not plain.lines[0].start_time and not plain.lines[0].end_time
    doc = make(start_time='09:00:00',end_time='10:30:00',hours=99)
    doc.reload()
    assert doc.lines[0].hours == doc.total_hours == 1.5
    doc.lines[0].end_time='11:00:00'
    doc.save()
    assert doc.lines[0].hours == doc.total_hours == 2
    doc.lines[0].start_time=None
    doc.save()
    assert doc.lines[0].hours == 2
    doc.lines[0].hours=1.25
    doc.save()
    assert doc.lines[0].hours == 1.25
    assert make(start_time='09:00:00',hours=0.75).lines[0].hours == 0.75
    assert make(end_time='10:00:00',hours=0.5).lines[0].hours == 0.5
    assert make(start_time='00:00:00',end_time='00:30:00',hours=0).lines[0].hours == 0.5
    assert entry_time.seconds(timedelta(0)) == 0
    assert entry_time.seconds(timedelta(hours=1)) == 3600
    for start,end in [('10:00','10:00'),('23:00','01:00'),('24:00','25:00'),('09:99','10:00'),('no','10:00')]:
        denied(lambda: make(start_time=start,end_time=end))
    denied(lambda: make(start_time='09:00',hours=0))
    # Time-derived rows must still respect the existing document hour cap.
    too_long=make(start_time='00:00',end_time='20:00')
    too_long.append('lines',dict(work_item='extra',result='Completed',hours=5))
    denied(too_long.save)
    # Submitting computed hours must preserve them and lock further time edits.
    doc.reload()
    review.transition(doc.name,'submit',str(doc.modified))
    doc.reload()
    doc.lines[0].start_time='08:00:00'
    denied(doc.save)
    print('ENTRY_TIME_PASS: persisted calculation, manual fallback, midnight, invalid ranges, total cap, review lock')
finally:
    frappe.db.rollback()
    frappe.set_user('Administrator')
