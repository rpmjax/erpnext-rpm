"""Isolated metadata migration proof; persists synthetic legacy targets only on the release fixture site."""
import hashlib,json
import frappe
from rpm_worklog import targets
frappe.init(site='analysis-fresh.internal');frappe.connect()
assert frappe.conf.get('rpm_worklog_managed')
frappe.set_user('Administrator')

def facts():
    return {table:hashlib.sha256(json.dumps(frappe.db.sql('SELECT * FROM `tab'+table+'` ORDER BY name',as_dict=True),default=str,sort_keys=True).encode()).hexdigest()
            for table in ('RPM Daily Work Log','RPM Work Log Line','RPM Work Log Review Event')}

try:
    for state in ('Open','Closed','Archived'):
        name='LIFECYCLE-LEGACY-'+state
        if not frappe.db.exists(targets.DT,name):
            frappe.db.sql('INSERT INTO `tabRPM Work Target` (name,target_name,owner,employee,status) VALUES (%s,%s,%s,%s,%s)',
                (name,name,'analysis-release-0@example.invalid','ARF-0',state))
    frappe.db.commit()
    before=facts()
    for run in range(2):
        targets.install();frappe.db.commit()
        assert facts()==before
        for state in ('Open','Closed','Archived'):
            row=frappe.db.get_value(targets.DT,'LIFECYCLE-LEGACY-'+state,['status','is_archived'],as_dict=True)
            assert row.status==state and bool(row.is_archived)==(state=='Archived')
    print('MIGRATION_PASS: legacy result not guessed, flag only, work facts unchanged, idempotent')
finally:
    frappe.db.rollback();frappe.destroy()
