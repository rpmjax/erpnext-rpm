app_name = "rpm_worklog"
app_title = "RPM Work Log"
app_publisher = "RPM"
app_description = "Employee work log review"
app_email = ""
app_license = "MIT"
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
