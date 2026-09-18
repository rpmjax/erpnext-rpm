// Preview only; the server repeats validation and computes the authoritative value.
function rpm_time_seconds(value) {
    if (value === null || value === undefined || value === '') return null;
    const match = String(value).match(/^(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?$/);
    if (!match) return NaN;
    const [hour, minute, second] = [Number(match[1]), Number(match[2]), Number(match[3] || 0)];
    if (hour > 23 || minute > 59 || second > 59) return NaN;
    return hour * 3600 + minute * 60 + second + Number('0.' + (match[4] || '0'));
}
function rpm_entry_duration(row) {
    const start = rpm_time_seconds(row.start_time), end = rpm_time_seconds(row.end_time);
    if (start === null || end === null) return null;
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return NaN;
    return flt((end - start) / 3600, precision('hours', row));
}
function rpm_preview_entry_time(frm, cdt, cdn) {
    if (['Pending Review', 'Approved'].includes(frm.doc.review_state)) return;
    const row = locals[cdt][cdn], hours = rpm_entry_duration(row);
    if (hours !== null && Number.isFinite(hours) && hours > 0 && Number(row.hours) !== hours) {
        return frappe.model.set_value(cdt, cdn, 'hours', hours);
    }
}
frappe.ui.form.on('RPM Work Log Line', {
    start_time: rpm_preview_entry_time,
    end_time: rpm_preview_entry_time,
    hours: rpm_preview_entry_time
});
frappe.ui.form.on('RPM Daily Work Log', {
    async validate(frm) {
        for (const row of frm.doc.lines || []) {
            const hours = rpm_entry_duration(row);
            if (hours !== null && (!Number.isFinite(hours) || hours <= 0)) {
                frappe.throw(`第 ${row.idx} 列：請確認結束時間晚於開始時間，且區間足以換算工時；跨午夜請拆列。`);
            }
            if (hours !== null && Number(row.hours) !== hours) {
                await frappe.model.set_value(row.doctype, row.name, 'hours', hours);
            }
        }
    }
});
