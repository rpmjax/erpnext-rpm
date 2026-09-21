import frappe, hashlib, json
from pathlib import Path
assert frappe.local.site == 'vm-release-check.internal'
mode=frappe.flags.get('upgrade_mode','before')
if mode=='before':
    from frappe.utils.file_manager import save_file
    if not frappe.db.exists('RPM Work Target',{'target_name':'Upgrade preservation fixture'}):
        old=frappe.get_all('RPM Daily Work Log',fields=['owner'],limit=1)[0]
        frappe.set_user(old.owner)
        t=frappe.get_doc(dict(doctype='RPM Work Target',target_name='Upgrade preservation fixture',status='Open')).insert()
        for private in (0,1):
            save_file('upgrade-check-'+str(private)+'.txt',b'nonempty upgrade preservation fixture',t.doctype,t.name,is_private=private)
        frappe.db.commit()
        frappe.set_user('Administrator')
result={}
for dt in ['Company','Department','User','Employee','RPM Daily Work Log','RPM Work Log Line','RPM Work Log Review Event','RPM Work Target','File','User Permission','Has Role']:
    rows=frappe.db.sql('SELECT * FROM `tab'+dt+'` ORDER BY name',as_dict=True)
    result[dt]=hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
result['auth']=hashlib.sha256(json.dumps(frappe.db.sql('SELECT * FROM __Auth ORDER BY doctype,name,fieldname'),default=str).encode()).hexdigest()
result['timezone']=frappe.db.get_single_value('System Settings','time_zone')
result['files']={}
for folder in ['public/files','private/files']:
    root=Path(frappe.get_site_path(folder))
    for p in root.rglob('*'):
        if p.is_file(): result['files'][str(p.relative_to(Path(frappe.get_site_path())))]=hashlib.sha256(p.read_bytes()).hexdigest()
path=Path(frappe.get_site_path('private','upgrade-check.json'))
if mode=='before':path.write_text(json.dumps(result));print('UPGRADE_BASELINE_SAVED',len(result['files']))
else:
    before=json.loads(path.read_text())
    assert before==result, [k for k in result if result[k]!=before.get(k)]
    print('UPGRADE_PRESERVATION_PASS: business data, targets, roles, permissions, auth, timezone and nonempty files unchanged')
