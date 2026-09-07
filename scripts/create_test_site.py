"""Create rpm-test.local on the inspected native v16 bench; never replace a site.

Run from the bench directory with env/bin/python after `sudo -v`.
Requires local MariaDB root socket access through sudo and installed ERPNext.
Uses the Frappe 16.33.0 installer API; review compatibility before other versions.
"""

import os
import secrets
import subprocess
from pathlib import Path

import frappe
from frappe.installer import _new_site


def main():
    bench = Path.cwd().resolve()
    site = "rpm-test.local"
    if not (bench / "sites" / "apps.txt").is_file():
        raise SystemExit("Run from the existing bench directory.")
    if (bench / "sites" / site).exists():
        raise SystemExit("Test site already exists; nothing changed.")
    if not (bench / "apps" / "erpnext").is_dir():
        raise SystemExit("ERPNext app is required.")
    subprocess.run(["sudo", "-n", "mariadb", "-e", "SELECT 1"],
                   check=True, stdout=subprocess.DEVNULL)
    private_dir = Path.home() / ".config" / "rpm-erpnext"
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    private_dir.chmod(0o700)
    credential_file = private_dir / "test-site-admin.txt"
    admin_password = secrets.token_urlsafe(24)
    # Exclusive creation protects credentials from an earlier/partial attempt.
    fd = os.open(credential_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(f"Site: {site}\nUser: Administrator\nPassword: {admin_password}\n")
    db_user = "rpm_setup_" + secrets.token_hex(4)
    db_password = secrets.token_hex(24)

    def sql(statement):
        subprocess.run(["sudo", "-n", "mariadb"], input=statement,
                       text=True, check=True, stdout=subprocess.DEVNULL)

    try:
        sql(f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY '{db_password}';"
            f"GRANT ALL PRIVILEGES ON *.* TO '{db_user}'@'localhost' WITH GRANT OPTION;")
        os.chdir(bench / "sites")
        frappe.init(site, new_site=True)
        _new_site(db_name=None, site=site, db_root_username=db_user,
                  db_root_password=db_password, admin_password=admin_password,
                  install_apps=["erpnext"], db_type="mariadb")
        print(f"Created {site}. Administrator credential is in {credential_file} (mode 600).")
    finally:
        frappe.destroy()
        sql(f"DROP USER IF EXISTS '{db_user}'@'localhost';")


if __name__ == "__main__":
    main()
