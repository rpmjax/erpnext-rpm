"""Administrator UI for the existing site-config key; no duplicate DB value."""
import json
import os
from pathlib import Path
import tempfile
import frappe

KEY = 'rpm_worklog_company'
DOCTYPE = 'RPM Worklog Settings'


def _authorize():
    user = frappe.session.user
    if user == 'Guest' or not frappe.db.get_value('User', user, 'enabled'):
        frappe.throw('Not permitted', frappe.PermissionError)
    if user != 'Administrator' and 'System Manager' not in frappe.get_roles():
        frappe.throw('System Manager required', frappe.PermissionError)


def _config_path():
    return Path(frappe.get_site_path('site_config.json'))


def _current_company():
    from frappe.config import get_site_config
    return get_site_config().get(KEY)


@frappe.whitelist()
def read():
    _authorize()
    return {'company': _current_company()}


@frappe.whitelist()
def search_companies(text=''):
    _authorize()
    if not isinstance(text, str) or len(text)>140:
        frappe.throw('Invalid company search')
    pattern = '%' + text.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_') + '%'
    rows = frappe.db.sql('SELECT name FROM `tabCompany` WHERE name LIKE %s ORDER BY name LIMIT 21', (pattern,), as_dict=True)
    return dict(items=[dict(value=r.name,label=r.name) for r in rows[:20]],has_more=len(rows)>20)


@frappe.whitelist(methods=['POST'])
def save(company, expected_company=None):
    _authorize()
    if not isinstance(company,str) or not company or len(company)>140 or not frappe.db.exists('Company', company):
        frappe.throw('Select an existing Company')
    if expected_company is not None and not isinstance(expected_company,str):
        frappe.throw('Invalid previous company')
    from frappe.utils.synchronization import filelock
    from frappe.config import clear_site_config_cache
    # Same lock as bench set-config. Check the disk value under the lock so two
    # administrators cannot silently overwrite each other's choice.
    with filelock('site_config'):
        if (_current_company() or '') != (expected_company or ''):
            frappe.throw('Company setting changed; reload before saving')
        path = _config_path()
        config = json.loads(path.read_text())
        config[KEY] = company
        fd, temporary = tempfile.mkstemp(prefix='.rpm-company-',dir=str(path.parent))
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(config,stream,ensure_ascii=False,indent=1,sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary,path.stat().st_mode & 0o777)
            os.replace(temporary,path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        clear_site_config_cache()
        frappe.conf[KEY]=company
    return {'company':company}


def install():
    exists = frappe.db.exists('DocType',DOCTYPE)
    doc = frappe.get_doc('DocType',DOCTYPE) if exists else frappe.get_doc(dict(
        doctype='DocType',name=DOCTYPE,module='Custom',custom=1,issingle=1,
        fields=[dict(fieldname='controls',label='Worklog Settings',fieldtype='HTML')]))
    if not any(p.role=='System Manager' for p in doc.permissions):
        doc.append('permissions',dict(role='System Manager',read=1))
    for permission in doc.permissions:
        if permission.role=='System Manager':
            permission.read=1
            for action in ('write','create','delete','submit','cancel','amend','share','export','import'):
                permission.set(action,0)
    doc.save() if exists else doc.insert()
    script = frappe.get_doc('Client Script',DOCTYPE) if frappe.db.exists('Client Script',DOCTYPE) else frappe.new_doc('Client Script')
    script.update(dict(name=DOCTYPE,dt=DOCTYPE,view='Form',enabled=1,
        script=(Path(__file__).parent/'public/js/settings.js').read_text(encoding='utf-8-sig')))
    script.save()
    frappe.db.after_commit.add(frappe.clear_cache)
