"""Run on a disposable/test Frappe site using the bench virtualenv.

Usage: env/bin/python /path/to/check_timesheet.py --site erpnext.local
Run from the bench directory. Test writes are rolled back, never committed.
This verifies native behavior as Administrator, not employee permissions or UI.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import frappe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    args = parser.parse_args()
    sites = Path.cwd() / "sites"
    if not (sites / args.site / "site_config.json").is_file():
        raise SystemExit("Run from a bench directory and specify an existing test site.")
    os.chdir(sites)
    frappe.init(site=args.site, sites_path=str(sites))
    frappe.connect()
    frappe.set_user("Administrator")
    before = frappe.db.count("Timesheet")
    results = []
    try:
        company = frappe.db.get_value("Company", {}, "name")
        if not company:
            raise RuntimeError("Site requires a configured company.")
        start = datetime(2026, 9, 7, 9)
        rows = []
        for hours in [2, 1.5, 0.5, 3, 1]:
            rows.append({"description": "RPM transactional verification", "from_time": start,
                         "hours": hours, "is_billable": 0})
            start += timedelta(hours=hours)
        doc = frappe.get_doc({"doctype": "Timesheet", "company": company,
                              "time_logs": rows})
        doc.insert()
        doc.submit()
        doc.reload()
        assert doc.docstatus == 1 and len(doc.time_logs) == 5
        assert doc.total_hours == 8
        assert all(not row.project and not row.task for row in doc.time_logs)
        assert not doc.employee
        results.append({"case": "five_rows_without_project_task_employee", "passed": True,
                        "total_hours": doc.total_hours, "docstatus": int(doc.docstatus)})
        frappe.db.rollback()

        no_time = frappe.get_doc({"doctype": "Timesheet", "company": company,
                                  "time_logs": [{"description": "Hours only", "hours": 1}]})
        try:
            no_time.insert()
            no_time.submit()
        except frappe.ValidationError as exc:
            results.append({"case": "hours_without_start_end", "accepted": False,
                            "reason": str(exc)})
        else:
            results.append({"case": "hours_without_start_end", "accepted": True})
    finally:
        frappe.db.rollback()
        after = frappe.db.count("Timesheet")
        assert before == after, "Timesheet count changed unexpectedly"
        frappe.destroy()
    print(json.dumps({"results": results, "rollback_verified": True,
                      "scope": "native server behavior only; permissions/UI not tested"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
