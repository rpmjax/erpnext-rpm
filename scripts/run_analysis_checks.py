"""Run candidate Python in a rollback-only local PoC process; no installation.

Usage: python scripts/run_analysis_checks.py CONTAINER [test_file ...]
Defaults to scripts/test_analysis_poc.py. Requires an already running PoC site.
"""
import base64
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
container = sys.argv[1]
tests = sys.argv[2:] or ['scripts/test_analysis_poc.py']
sources = {name:(root/'apps/rpm_worklog/rpm_worklog'/f'{name}.py').read_text(encoding='utf-8-sig')
           for name in ('scope','analysis','analysis_export','reports','settings')}
sources['tests'] = [(test,(root/test).read_text(encoding='utf-8-sig')) for test in tests]
payload = base64.b64encode(json.dumps(sources).encode()).decode()
code = '''import base64,json,sys,types
import frappe
frappe.init(site='frontend')
frappe.connect()
assert frappe.conf.get('rpm_worklog_model_poc'), 'PoC only'
source=json.loads(base64.b64decode(PAYLOAD))
import rpm_worklog
for name in ('scope','analysis','analysis_export','reports','settings'):
    module=types.ModuleType('rpm_worklog.'+name)
    module.__file__='/home/frappe/frappe-bench/apps/rpm_worklog/rpm_worklog/'+name+'.py'
    sys.modules[module.__name__]=module
    exec(compile(source[name],name+'.py','exec'),module.__dict__)
    setattr(rpm_worklog,name,module)
try:
    for path, text in source['tests']:
        exec(compile(text,path,'exec'),{'__name__':'__main__'})
        print('PASS',path)
finally:
    frappe.db.rollback()
    frappe.destroy()
'''.replace('PAYLOAD',repr(payload))
result = subprocess.run(['docker','exec','-i','-w','/home/frappe/frappe-bench/sites',
    container,'/home/frappe/frappe-bench/env/bin/python','-'],input=code.encode())
sys.exit(result.returncode)
