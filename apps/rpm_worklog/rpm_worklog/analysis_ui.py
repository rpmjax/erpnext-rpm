"""Install the analysis entry on the existing Analytics form, no new dataset DocType."""
from pathlib import Path
import frappe
from rpm_worklog.scope import install_analysis_role, MANAGEMENT_ROLE


def install():
    install_analysis_role()
    viewer='RPM Work Log Analytics'
    doc=frappe.get_doc('DocType',viewer)
    if not any(p.role==MANAGEMENT_ROLE for p in doc.permissions):
        doc.append('permissions',dict(role=MANAGEMENT_ROLE,read=1,write=0,create=0))
    for permission in doc.permissions:
        if permission.role==MANAGEMENT_ROLE:
            permission.read=1
            for action in ('write','create','delete','submit','cancel','amend','share','export','import'):
                permission.set(action,0)
    doc.save()
    root=Path(__file__).parent/'public'/'js'
    source='\n'.join((root/name).read_text(encoding='utf-8-sig') for name in ('analytics.js','analysis.js'))
    script=frappe.get_doc('Client Script',viewer) if frappe.db.exists('Client Script',viewer) else frappe.new_doc('Client Script')
    script.update(dict(name=viewer,dt=viewer,view='Form',enabled=1,script=source))
    script.save()
    frappe.db.after_commit.add(frappe.clear_cache)
