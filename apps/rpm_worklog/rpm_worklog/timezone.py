"""Timezone policy only for deployments explicitly marked at fresh creation."""
import frappe

TARGET = 'Asia/Taipei'


def is_fresh_setup():
    return (frappe.conf.get('rpm_worklog_fresh_timezone') == TARGET
            and not frappe.db.get_single_value('System Settings', 'setup_complete'))


def validate_settings(doc, method=None):
    # No marker is added by install/migrate/update. Completed sites are untouched.
    if is_fresh_setup():
        doc.time_zone = TARGET


def setup_stages(args):
    # Frappe constructs all stages before executing the first global-settings task.
    # Keep its args consistent, including its standard-user timezone background job.
    if is_fresh_setup():
        args['timezone'] = TARGET
    return []


def initialize():
    if not is_fresh_setup():
        frappe.throw('Timezone initialization requires an explicitly marked fresh, unfinished site')
    # Before the wizard, unrelated mandatory settings (e.g. language) are blank.
    # Set only the requested timezone and its Frappe default, not other settings.
    frappe.db.set_single_value('System Settings', 'time_zone', TARGET)
    frappe.db.set_default('time_zone', TARGET)
    from frappe.core.doctype.system_settings.system_settings import clear_system_settings_cache
    clear_system_settings_cache()
    frappe.db.after_commit.add(frappe.clear_cache)
    verify()


def verify():
    actual = frappe.db.get_single_value('System Settings', 'time_zone')
    if actual != TARGET:
        frappe.throw('Fresh Frappe System Settings timezone verification failed')
    print('Frappe System Settings timezone -> Asia/Taipei -> PASS')
