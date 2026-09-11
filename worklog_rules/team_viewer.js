frappe.ui.form.on('RPM Team Work Log Viewer', {
    refresh(frm) {
        frm.disable_save();
        frm.add_custom_button('查詢', () => load_team(frm));
        if (!frm.doc.from_date) frm.doc.from_date = frappe.datetime.get_today();
        if (!frm.doc.to_date) frm.doc.to_date = frappe.datetime.get_today();
        frm.refresh_fields();
        frm.fields_dict.results.$wrapper.html('<p>選擇日期後按「查詢」。此頁僅供查閱，不可修改員工紀錄。</p>');
    }
});
function load_team(frm) {
    const target = frm.fields_dict.results.$wrapper;
    target.empty().text('查詢中…');
    frappe.call('rpm_team_worklogs', {from_date:frm.doc.from_date,to_date:frm.doc.to_date}).then(r => {
        const data = r.message;
        const esc = value => frappe.utils.escape_html(String(value ?? ''));
        let html = `<p>有效直屬員工 ${data.direct_report_count} 位；本次顯示 ${data.logs.length} 張。${data.truncated ? '超過 300 張，請縮小日期範圍。' : ''}</p>`;
        for (const log of data.logs) {
            html += `<details style="margin-bottom:16px"><summary>${esc(log.work_date)} | ${esc(log.employee_name)} | ${esc(log.department)} | ${esc(log.title)} | ${esc(log.total_hours)} 小時 | ${esc(log.name)}</summary><div class="table-responsive"><table class="table table-bordered"><thead><tr><th>分類</th><th>工作內容</th><th>數量</th><th>單位</th><th>結果</th><th>工時</th><th>備註</th></tr></thead><tbody>`;
            for (const row of log.lines) html += `<tr><td>${esc(row.activity_type)}</td><td>${esc(row.work_item)}</td><td>${row.record_quantity ? esc(row.quantity) : ''}</td><td>${esc(row.uom)}</td><td>${esc(row.result)}</td><td>${esc(row.hours)}</td><td>${esc(row.note)}</td></tr>`;
            html += '</tbody></table></div></details>';
        }
        target.html(html);
    }).catch(() => target.empty().text('查詢失敗，請查看錯誤訊息後重試。'));
}
