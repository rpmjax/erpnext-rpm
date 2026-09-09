"""Run only through bench console on the isolated Docker PoC site.

Model prototype only: System Manager access, no employee rollout or approval.
No Custom App, core patches, server scripts or Timesheet changes.
"""
import frappe

if frappe.local.site != "frontend" or not frappe.conf.get("rpm_worklog_model_poc"):
    raise RuntimeError("Requires explicitly marked Docker PoC site frontend")


def field(name, label, kind, **kwargs):
    return dict(fieldname=name, label=label, fieldtype=kind, **kwargs)


definitions = [
    dict(
        name="RPM Work Log Line", istable=1, editable_grid=1,
        fields=[
            field("activity_type", "Activity Type", "Link", options="Activity Type", in_list_view=1),
            field("work_item", "Work Item", "Data", reqd=1, in_list_view=1),
            field("quantity", "Completed Quantity", "Float", in_list_view=1),
            field("uom", "UOM", "Link", options="UOM", in_list_view=1),
            field("result", "Result", "Select", options="In Progress\nCompleted\nBlocked", reqd=1, in_list_view=1),
            field("hours", "Hours", "Float", reqd=1, in_list_view=1),
            field("note", "Note", "Small Text"),
        ],
    ),
    dict(
        name="RPM Daily Work Log", autoname="format:RWL-{YYYY}-{#####}",
        title_field="title", track_changes=1,
        fields=[
            field("title", "Title", "Data", reqd=1),
            field("work_date", "Work Date", "Date", default="Today", reqd=1, in_list_view=1),
            field("employee", "Employee", "Link", options="Employee", reqd=1, in_list_view=1),
            field("department", "Department", "Link", options="Department", fetch_from="employee.department", read_only=1),
            field("lines", "Work Entries", "Table", options="RPM Work Log Line", reqd=1),
        ],
        permissions=[dict(role="System Manager", read=1, write=1, create=1, report=1, export=1)],
    ),
]
for definition in definitions:
    if not frappe.db.exists("DocType", definition["name"]):
        frappe.get_doc(dict(doctype="DocType", module="Custom", custom=1, **definition)).insert()

# Synthetic masters only, no source-site data or real employee identities.
if not frappe.db.exists("Warehouse Type", "Transit"):
    frappe.get_doc(dict(doctype="Warehouse Type", name="Transit")).insert()
if not frappe.db.exists("Company", "RPM Model PoC"):
    frappe.get_doc(dict(doctype="Company", company_name="RPM Model PoC", abbr="RMP",
                        default_currency="TWD", country="Taiwan")).insert()
if not frappe.db.exists("Activity Type", "PoC Assembly"):
    frappe.get_doc(dict(doctype="Activity Type", activity_type="PoC Assembly")).insert()
if not frappe.db.exists("UOM", "PoC Piece"):
    frappe.get_doc(dict(doctype="UOM", uom_name="PoC Piece", must_be_whole_number=1)).insert()
employee = frappe.db.get_value("Employee", {"employee_number": "MODEL-POC-001"}, "name")
if not frappe.db.exists("Gender", "Male"):
    frappe.get_doc(dict(doctype="Gender", gender="Male")).insert()
if not employee:
    employee = frappe.get_doc(dict(doctype="Employee", first_name="Model PoC Employee",
        employee_number="MODEL-POC-001", company="RPM Model PoC", gender="Male",
        date_of_birth="1990-01-01", date_of_joining="2026-09-09", status="Active")).insert().name
existing = frappe.db.get_value("RPM Daily Work Log", {"title": "Model PoC - assembly 5 pieces"}, "name")
if not existing:
    existing = frappe.get_doc(dict(doctype="RPM Daily Work Log",
        title="Model PoC - assembly 5 pieces", work_date="2026-09-09", employee=employee,
        lines=[dict(activity_type="PoC Assembly", work_item="Rear shock absorber assembly",
            quantity=5, uom="PoC Piece", result="Completed", hours=1,
            note="Synthetic model test only; not a production or attendance record.")])).insert().name
frappe.db.commit()
saved = frappe.get_doc("RPM Daily Work Log", existing)
assert saved.lines[0].quantity == 5 and saved.lines[0].hours == 1
assert saved.lines[0].result == "Completed"
assert not frappe.get_meta("RPM Work Log Line").has_field("from_time")
print("MODEL_POC_OK " + saved.name)
