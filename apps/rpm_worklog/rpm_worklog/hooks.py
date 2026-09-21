app_name = "rpm_worklog"
app_title = "RPM Work Log"
app_publisher = "RPM"
app_description = "Employee work log review"
app_email = ""
app_license = "MIT"
notification_skip_email_types = ['RPM Work Log Review']
after_install = "rpm_worklog.setup.install"
after_migrate = "rpm_worklog.setup.install"
doc_events = {
    "RPM Daily Work Log": {
        "before_validate": "rpm_worklog.review.validate",
        "on_trash": "rpm_worklog.review.prevent_delete",
    },
    "RPM Work Log Review Event": {
        "before_insert": "rpm_worklog.review.protect_event",
        "before_save": "rpm_worklog.review.protect_event",
        "on_trash": "rpm_worklog.review.protect_event",
    },
}

doc_events['RPM Work Log Report'] = {'validate': 'rpm_worklog.reports.validate_config'}

doc_events['System Settings'] = {'before_validate': 'rpm_worklog.timezone.validate_settings'}
setup_wizard_stages = 'rpm_worklog.timezone.setup_stages'

doc_events['RPM Work Target'] = {'validate': 'rpm_worklog.targets.validate', 'on_trash':'rpm_worklog.targets.prevent_delete'}
has_permission = {'RPM Work Target':'rpm_worklog.targets.has_permission'}
permission_query_conditions = {'RPM Work Target':'rpm_worklog.targets.permission_query'}

app_include_js = ['/assets/rpm_worklog/js/sidebar.js']
