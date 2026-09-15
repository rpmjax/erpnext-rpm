"""Run only on the disposable timezone.internal installation test."""
import frappe
from rpm_worklog import timezone
from frappe.desk.page.setup_wizard.setup_wizard import get_setup_stages, update_system_settings
assert frappe.local.site=='timezone.internal' and frappe.conf.get('rpm_worklog_fresh_timezone')=='Asia/Taipei'
frappe.local.lang='en'
timezone.verify()
args=frappe._dict(country='Taiwan',currency='TWD',language='English',timezone='Africa/Abidjan')
get_setup_stages(args)
assert args.timezone=='Asia/Taipei'
# Even the wizard's early settings endpoint cannot persist the accidental value.
settings=frappe.get_single('System Settings')
settings.language='en'
settings.time_zone='Africa/Abidjan'
settings.save()
assert settings.time_zone=='Asia/Taipei'
update_system_settings(args)
timezone.verify()
settings=frappe.get_single('System Settings')
settings.setup_complete=1
settings.save()
settings.time_zone='Pacific/Auckland'
settings.save()
assert settings.time_zone=='Pacific/Auckland'
args.timezone='Pacific/Auckland'
get_setup_stages(args)
assert args.timezone=='Pacific/Auckland'
try:
    timezone.initialize()
except frappe.ValidationError:
    pass
else:
    raise AssertionError('Completed site initialization was accepted')
# Existing unmarked site is untouched even if setup_complete is false.
frappe.conf.pop('rpm_worklog_fresh_timezone',None)
settings.setup_complete=0
settings.save()
assert settings.time_zone=='Pacific/Auckland'
settings.setup_complete=1
settings.save()
frappe.db.commit()
print('TIMEZONE_GUARDS_PASS: fresh wizard protected; completed and unmarked settings preserved')
