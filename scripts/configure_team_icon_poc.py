"""Install a recolored native Frappe users SVG for the manager desktop entry."""
from pathlib import Path
import frappe
from frappe.utils.file_manager import save_file
assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')
assert frappe.session.user == 'Administrator'
label = '直屬員工工作紀錄'
content = Path('/tmp/team-worklogs-yellow.svg').read_text()
file = save_file('rpm-team-worklogs-yellow.svg', content, 'Desktop Icon', label, is_private=0)
icon = frappe.get_doc('Desktop Icon', label)
icon.icon_image = file.file_url
icon.logo_url = file.file_url
icon.save()
frappe.db.commit()
frappe.clear_cache()
print('TEAM_ICON_UPDATED', file.file_url)
