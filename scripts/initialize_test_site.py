"""Initialize only rpm-test.local with synthetic company data; run from bench."""

import os
from datetime import date
from pathlib import Path

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete


def main():
    sites = Path.cwd() / "sites"
    if not (sites / "rpm-test.local" / "site_config.json").is_file():
        raise SystemExit("Run from the bench containing rpm-test.local.")
    os.chdir(sites)
    frappe.init(site="rpm-test.local", sites_path=str(sites))
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.flags.mute_emails = True
    try:
        if frappe.is_setup_complete():
            print("Test site already initialized; nothing changed.")
            return
        language = frappe.db.get_value("Language", "zh-TW", "language_name")
        if not language:
            raise RuntimeError("zh-TW language not installed.")
        year = date.today().year
        result = setup_complete({
            "language": language, "lang": language,
            "country": "Taiwan", "currency": "TWD", "timezone": "Asia/Taipei",
            "company_name": "RPM Test Company", "company_abbr": "RPMTEST",
            "chart_of_accounts": "Standard", "fy_start_date": f"{year}-01-01",
            "fy_end_date": f"{year}-12-31", "setup_demo": 0, "enable_telemetry": 0,
        })
        assert result and result.get("status") == "ok", result
        frappe.db.commit()
        assert frappe.is_setup_complete()
        print("Test setup complete: RPM Test Company / zh-TW / Asia/Taipei / TWD.")
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()
