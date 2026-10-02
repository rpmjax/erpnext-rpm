"""Settings authorization and real temporary-file writes; never edit site_config."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import frappe
from rpm_worklog import settings

assert frappe.local.site == 'frontend' and frappe.conf.get('rpm_worklog_model_poc')

def denied(fn):
    try:
        fn()
    except (frappe.PermissionError, frappe.ValidationError):
        return
    raise AssertionError('Expected denial')

original_user = frappe.session.user
original_company = frappe.conf.get('rpm_worklog_company')
try:
    company = frappe.get_all('Company',pluck='name',limit=1)[0]
    user = frappe.get_all('User',filters={'enabled':1,'name':['not in',['Guest','Administrator']]},pluck='name',limit=1)[0]
    with TemporaryDirectory() as directory:
        path = Path(directory)/'site_config.json'
        path.write_text(json.dumps({'db_password':'test-secret','unrelated':True}))
        with patch.object(settings,'_config_path',return_value=path), patch.object(settings,'_current_company',side_effect=lambda:json.loads(path.read_text()).get(settings.KEY)):
            frappe.set_user(user)
            with patch.object(frappe,'get_roles',return_value=['RPM Worklog Management']):
                denied(settings.read)
                denied(lambda:settings.save(company,None))
                denied(lambda:settings.search_companies(''))
            frappe.set_user('Guest')
            denied(settings.read)
            frappe.set_user('Administrator')  # No Employee needed for settings maintenance.
            assert settings.read()['company'] is None
            denied(lambda:settings.save('MISSING COMPANY',None))
            denied(lambda:settings.save('',None))
            result=settings.save(company,None)
            assert result['company']==company
            assert json.loads(path.read_text())=={'db_password':'test-secret','unrelated':True,settings.KEY:company}
            assert settings.read()['company']==company
            denied(lambda:settings.save(company,'STALE COMPANY'))
            with patch.object(settings.os,'replace',side_effect=OSError('disk failure')):
                try:
                    settings.save(company,company)
                except OSError:
                    pass
                else:
                    raise AssertionError('Expected I/O failure')
            assert json.loads(path.read_text())[settings.KEY]==company
            frappe.set_user(user)
            with patch.object(frappe,'get_roles',return_value=['System Manager']):
                assert settings.save(company,company)['company']==company
                assert any(c['value']==company for c in settings.search_companies(company)['items'])
    print('SETTINGS_PASS: Administrator/System Manager only, no Employee dependency, validation, stale-write rejection, preserve other keys, atomic failure')
finally:
    frappe.conf.rpm_worklog_company=original_company
    frappe.db.rollback()
    frappe.set_user(original_user)
