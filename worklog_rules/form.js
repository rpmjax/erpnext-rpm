frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) { refresh_daily(frm); },
    after_save(frm) { refresh_daily(frm); },
    work_date(frm) { refresh_daily(frm); }
});
function refresh_daily(frm) {
    if (!frm.doc.work_date || !frappe.user_roles.includes('RPM Work Log Pilot')) return;
    const date = frm.doc.work_date;
    frappe.call('rpm_worklog_daily_summary', {work_date: date}).then(r => {
        if (date !== frm.doc.work_date || !r.message) return;
        const d = r.message;
        frm.set_intro(`本人 ${frappe.utils.escape_html(date)} 已保存 ${d.record_count} 張，共 ${d.total_hours} 小時（未含未保存修改）。` +
            (d.total_hours > 24 ? ' 超過 24 小時，請檢查是否重複計時。' : ''), d.total_hours > 24 ? 'orange' : 'blue');
    });
}
