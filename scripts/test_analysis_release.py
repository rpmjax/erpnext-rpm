"""Synthetic full-image release checks. Run inside the isolated site's bench.

python /tmp/test_analysis_release.py SITE seed|before|check
Only the two explicitly named disposable release sites are accepted.
seed commits synthetic fixtures; before saves a fingerprint; check is read-only
apart from rollback-only service tests. No candidate module injection is used.
Copy test_analysis_poc.py and test_worklog_settings_poc.py alongside this script before check.
"""
import hashlib
import json
from pathlib import Path
import sys

import frappe

site, mode = sys.argv[1:]
assert site in ('analysis-fresh.internal', 'analysis-upgrade.internal')
assert mode in ('seed', 'before', 'check')
frappe.init(site=site)
frappe.connect()
assert frappe.conf.get('rpm_worklog_managed')
frappe.set_user('Administrator')


def fingerprint():
    result = {}
    for table in ('Company', 'Department', 'User', 'Employee', 'RPM Daily Work Log',
                  'RPM Work Log Line', 'RPM Work Target', 'RPM Work Log Review Event',
                  'User Permission', 'Has Role', 'File'):
        rows = frappe.db.sql('SELECT * FROM `tab' + table + '` ORDER BY name', as_dict=True)
        result[table] = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
    result['auth'] = hashlib.sha256(json.dumps(frappe.db.sql(
        'SELECT * FROM __Auth ORDER BY doctype,name,fieldname'), default=str).encode()).hexdigest()
    result['timezone'] = frappe.db.get_single_value('System Settings', 'time_zone')
    root = Path(frappe.get_site_path())
    result['files'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for folder in ('public/files', 'private/files')
                       for p in (root / folder).rglob('*') if p.is_file()}
    return result


try:
    if mode == 'seed':
        # Minimal synthetic SQL fixtures, not an ERPNext company setup demonstration.
        assert not frappe.db.count('Employee'), 'Refuse to seed an existing business dataset'
        company = 'Analysis Release Fixture'
        frappe.db.sql('INSERT INTO `tabCompany` (name,company_name,abbr) VALUES (%s,%s,%s)',
                      (company, company, 'ARF'))
        for i in range(5):
            user = f'analysis-release-{i}@example.invalid'
            frappe.get_doc(dict(doctype='User', email=user, first_name=f'Fixture {i}',
                                enabled=1, send_welcome_email=0)).insert()
            frappe.db.sql('''INSERT INTO `tabEmployee`
                (name,employee_name,user_id,company,status,employee_number)
                VALUES (%s,%s,%s,%s,'Active',%s)''',
                (f'ARF-{i}', f'Fixture {i}', user, company, f'ARF{i}'))
        frappe.db.sql('''INSERT INTO `tabRPM Daily Work Log`
            (name,owner,employee,employee_name,title,work_date,total_hours,review_state,docstatus)
            VALUES ('ARF-LOG','analysis-release-0@example.invalid','ARF-0','Fixture 0',
            'Preservation fixture','2026-10-01',8.4,'Draft',0)''')
        for idx, hours in ((1, 8), (2, .4)):
            frappe.db.sql('''INSERT INTO `tabRPM Work Log Line`
                (name,parent,parenttype,parentfield,idx,work_item,hours,result)
                VALUES (%s,'ARF-LOG','RPM Daily Work Log','lines',%s,'Fixture',%s,'In Progress')''',
                (f'ARF-LINE-{idx}', idx, hours))
        from frappe.utils.file_manager import save_file
        for private in (0, 1):
            save_file(f'analysis-release-{private}.txt', b'nonempty preservation fixture',
                      'RPM Daily Work Log', 'ARF-LOG', is_private=private)
        frappe.db.commit()
        print('SYNTHETIC_SEED_PASS: 5 employees, 1 log, 2 lines, 8.4h, 2 attachments')
    elif mode == 'before':
        Path(frappe.get_site_path('private', 'analysis-release-baseline.json')).write_text(
            json.dumps(fingerprint()))
        print('PRESERVATION_BASELINE_SAVED')
    else:
        baseline = Path(frappe.get_site_path('private', 'analysis-release-baseline.json'))
        assert baseline.exists()
        expected = json.loads(baseline.read_text())
        assert fingerprint() == expected, 'Business data changed across migration'
        from rpm_worklog import analysis, scope
        assert all(app in frappe.get_installed_apps() for app in ('frappe', 'erpnext', 'rpm_worklog'))
        assert frappe.db.exists('Role', scope.MANAGEMENT_ROLE)
        perms = frappe.get_doc('DocType', 'RPM Work Log Analytics').permissions
        perm = next(p for p in perms if p.role == scope.MANAGEMENT_ROLE)
        assert perm.read and not any(perm.get(a) for a in
            ('write','create','delete','submit','cancel','amend','share','export','import'))
        root = Path(analysis.__file__).parent / 'public/js'
        expected_js = '\n'.join((root / f).read_text(encoding='utf-8-sig')
                                for f in ('analytics.js', 'analysis.js'))
        assert frappe.db.get_value('Client Script', 'RPM Work Log Analytics', 'script') == expected_js
        from rpm_worklog import settings
        settings_doc = frappe.get_doc('DocType', settings.DOCTYPE)
        assert settings_doc.issingle
        assert not any(f.fieldtype != 'HTML' for f in settings_doc.fields)
        settings_perm = next(p for p in settings_doc.permissions if p.role == 'System Manager')
        assert settings_perm.read and not any(settings_perm.get(a) for a in
            ('write','create','delete','submit','cancel','amend','share','export','import'))
        assert frappe.db.get_value('Client Script', settings.DOCTYPE, 'script') == (root / 'settings.js').read_text(encoding='utf-8-sig')
        # The original suite is guarded for the local PoC; substitute only that
        # guard after the stricter disposable-site assertion above. Import real image code.
        source = Path(__file__).with_name('test_analysis_poc.py').read_text(encoding='utf-8-sig')
        guard = "assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')"
        assert source.count(guard) == 1
        exec(compile(source.replace(guard, 'assert frappe.local.site == ' + repr(site)),
                     'test_analysis_poc.py', 'exec'), {'__name__': '__main__'})
        source = Path(__file__).with_name('test_worklog_settings_poc.py').read_text(encoding='utf-8-sig')
        assert source.count(guard) == 1
        exec(compile(source.replace(guard, 'assert frappe.local.site == ' + repr(site)),
                     'test_worklog_settings_poc.py', 'exec'), {'__name__': '__main__'})
        assert fingerprint() == expected, 'Rollback tests changed fixtures'
        print('RELEASE_CHECK_PASS: installed apps, read-only role, exact client script, service suite, preservation')
finally:
    frappe.db.rollback()
    frappe.destroy()
