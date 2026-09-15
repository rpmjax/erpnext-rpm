"""Fresh-site initialization only; reruns never restore or overwrite a site."""
import json
import os
from pathlib import Path
import subprocess

site = os.environ['RPM_SITE']
if not site or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789.-' for c in site):
    raise SystemExit('RPM_SITE must be a lower-case DNS name')

def bench(*args):
    result = subprocess.run(['bench', *args])
    if result.returncode:
        raise SystemExit('Initialization step failed; inspect preceding error. Secrets omitted.')

sites = Path('/home/frappe/frappe-bench/sites')
path = sites / site
if path.exists():
    raise SystemExit('Site already exists. Use status/update; initialization will not overwrite it.')
(sites / 'apps.txt').write_text('frappe\nerpnext\nrpm_worklog\n')
common = sites / 'common_site_config.json'
config = json.loads(common.read_text()) if common.exists() else {}
config.update(db_host='db',db_port=3306,redis_cache='redis://redis-cache:6379',
              redis_queue='redis://redis-queue:6379',redis_socketio='redis://redis-queue:6379',socketio_port=9000)
common.write_text(json.dumps(config,indent=2))
bench('new-site', site, '--db-root-username','root',
      '--db-root-password',Path('/run/secrets/db_password').read_text().strip(),
      '--admin-password',Path('/run/secrets/admin_password').read_text().strip(),
      '--mariadb-user-host-login-scope','%')
bench('--site',site,'install-app','erpnext')
bench('--site',site,'set-config','rpm_worklog_managed','1','--parse')
bench('--site',site,'set-config','mute_emails','True','--parse')
bench('--site',site,'install-app','rpm_worklog')
bench('--site',site,'migrate')
print('RPM_INIT_SUCCESS: complete ERPNext setup wizard and enroll employees before use')
