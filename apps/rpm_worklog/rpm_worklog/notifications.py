"""Transactional in-app review notifications; no email or background worker required."""
from urllib.parse import quote, urlencode
import frappe
from frappe.desk.doctype.notification_settings.notification_settings import is_notifications_enabled

TYPE = 'RPM Work Log Review'


def install():
    if not frappe.db.exists('Notification Type', TYPE):
        frappe.get_doc(dict(doctype='Notification Type',type_name=TYPE,enabled=1)).insert()


def notify_review(doc, event, manager_user=None):
    recipient = manager_user if event.action == 'submit' else doc.owner
    if not recipient or not frappe.db.get_value('User',recipient,'enabled') or not is_notifications_enabled(recipient):
        return
    if not frappe.db.get_value('Notification Type',TYPE,'enabled'):
        return
    name = 'rpm-review-' + event.name
    if frappe.db.exists('Notification Log',name):
        return
    if event.action == 'submit':
        title = '工作紀錄重新送審' if event.from_state == 'Returned' else '工作紀錄待審核'
        link = '/desk/rpm-team-work-log-viewer/RPM%20Team%20Work%20Log%20Viewer?' + urlencode(
            dict(work_date=str(doc.work_date),work_log=doc.name))
    else:
        title = '工作紀錄已退回，請補正' if event.action == 'return' else '工作紀錄已核准'
        link = '/desk/rpm-daily-work-log/' + quote(doc.name,safe='')
    # Keep persistent notifications minimal; details are fetched with current permissions on click.
    description = frappe.utils.escape_html(f'{doc.name} · {doc.work_date}。請開啟頁面查看目前狀態。')
    frappe.get_doc(dict(doctype='Notification Log',type=TYPE,title=title,description=description,
        for_user=recipient,from_user=frappe.session.user,app='rpm_worklog',link=link,
        document_type=doc.doctype,document_name=doc.name,
        source_doctype=event.doctype,source_name=event.name)).insert(ignore_permissions=True,set_name=name)
