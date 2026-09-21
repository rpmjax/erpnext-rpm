"""Run via bench console after migration, before browser acceptance."""
from pathlib import Path
import frappe
import rpm_worklog
source = Path(rpm_worklog.__file__).parent / 'public' / 'js' / 'team_review.js'
actual = frappe.db.get_value('Client Script', 'RPM Team Viewer', ['enabled', 'script'], as_dict=True)
assert actual and actual.enabled, 'Team viewer Client Script is disabled or missing'
assert actual.script == source.read_text(encoding='utf-8-sig'), 'Stale Client Script: run site migrate before acceptance'
assert 'frappe.route_options' in actual.script and 'work_log=null' in actual.script
print('TEAM_VIEWER_DEPLOYMENT_PASS: active database Client Script matches image source')
