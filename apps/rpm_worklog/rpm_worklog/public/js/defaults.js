frappe.ui.form.on('RPM Daily Work Log', {
    async onload(frm) {
        if (!frappe.user_roles.includes('RPM Work Log Pilot')) return;
        if (frm.is_new()) {
            const {message: emp} = await frappe.call('rpm_worklog.queries.defaults');
            await frm.set_value('employee',emp.name);
            await frm.set_value('department',emp.department);
            if (!frm.doc.title) await frm.set_value('title','Work Log '+frm.doc.work_date);
        }
    },
    refresh(frm) {
        if (frappe.user_roles.includes('RPM Work Log Pilot')) frm.set_df_property('employee','read_only',1);
        rpm_daily_total(frm);
    },
    work_date(frm) { rpm_daily_total(frm); }
});
function rpm_daily_total(frm) {
    if (!frm.doc.work_date || !frappe.user_roles.includes('RPM Work Log Pilot')) return;
    const date=frm.doc.work_date;
    frappe.call('rpm_worklog.queries.daily_summary',{work_date:date}).then(({message:d}) => {
        if (frm.doc.work_date === date) frm.dashboard.set_headline_alert(`本人 ${frappe.utils.escape_html(date)} 已保存 ${d.count} 張，共 ${Number(d.hours).toFixed(3)} 小時（未含未保存修改）。`);
    });
}
