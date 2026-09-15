"""Run through bench console on an explicitly managed test site."""
import time
import uuid
import frappe
from frappe.utils.background_jobs import enqueue
assert frappe.conf.get('rpm_worklog_managed')
jobs = [enqueue('frappe.utils.now',queue=q,job_id='rpm-queue-check-'+q+'-'+uuid.uuid4().hex,is_async=True) for q in ('short','default','long')]
for job in jobs:
    for attempt in range(30):
        if job.get_status(refresh=True) in ('finished','failed'): break
        time.sleep(1)
    assert job.get_status(refresh=True)=='finished', (job.id,job.get_status())
print('QUEUE_JOBS_PASS: short, default, long all finished')
