frappe.ui.form.on('RPM Team Work Log Viewer', {
    refresh(frm) {
        frm.disable_save();
        // Query controls are transient HTML inputs, never saved document fields.
        frm.set_df_property('from_date', 'hidden', 1);
        frm.set_df_property('to_date', 'hidden', 1);
        frm.doc.__unsaved = 0;
        frm.page.set_indicator('唯讀查詢', 'blue');
        const wrapper = frm.fields_dict.results.$wrapper;
        wrapper.html(`<nav aria-label="頁面導覽" style="margin-bottom:16px"><a class="btn btn-default" href="/desk">← 返回首頁</a></nav><p>選擇日期後按下方「查詢」。此頁不需要保存。</p>
            <div class="row">
                <div class="col-sm-4"><label>開始日期 <input type="date" class="form-control team-from"></label></div>
                <div class="col-sm-4"><label>結束日期 <input type="date" class="form-control team-to"></label></div>
            </div>
            <button type="button" class="btn btn-primary team-query" style="margin:12px 0">查詢</button>
            <div class="team-results" aria-live="polite"></div>`);
        wrapper.find('.team-from, .team-to').val(frappe.datetime.get_today());
        const query = () => {
            const from = wrapper.find('.team-from').val();
            const to = wrapper.find('.team-to').val();
            if (!from || !to) { frappe.msgprint('請填寫開始與結束日期'); return; }
            load_team(frm, from, to);
        };
        wrapper.find('.team-query').on('click', query);
        frm.page.set_primary_action('查詢', query);
    }
});
function load_team(frm, from_date, to_date) {
    const target = frm.fields_dict.results.$wrapper.find('.team-results');
    target.empty().text('查詢中…');
    frappe.call('rpm_team_worklogs', {from_date, to_date}).then(r => {
        const data = r.message;
        const esc = value => frappe.utils.escape_html(String(value ?? ''));
        let html = `<p>有效直屬員工 ${data.direct_report_count} 位；本次顯示 ${data.logs.length} 張。${data.truncated ? '超過 300 張，請縮小日期範圍。' : ''}</p>`;
        for (const log of data.logs) {
            html += `<details style="margin-bottom:16px"><summary>${esc(log.work_date)} | ${esc(log.employee_name)} | ${esc(log.department)} | ${esc(log.title)} | ${esc(log.total_hours)} 小時 | ${esc(log.name)} | ${esc(__(log.review_state || 'Draft'))}</summary><div class="table-responsive"><table class="table table-bordered"><thead><tr><th>分類</th><th>工作內容</th><th>關聯物料</th><th>數量</th><th>結果</th><th>工時</th><th>備註</th></tr></thead><tbody>`;
            for (const row of log.lines) html += `<tr><td>${esc(row.activity_type)}</td><td>${esc(row.work_item)}</td><td>${esc(row.item_code)} ${esc(row.item_name_snapshot)}</td><td>${esc(row.quantity)}</td><td>${esc(row.result)}</td><td>${esc(row.hours)}</td><td>${esc(row.note)}</td></tr>`;
                        html += '</tbody></table></div>';
            const index = data.logs.indexOf(log);
            if (log.review_state === 'Pending Review') html += `<p><button class="btn btn-primary review-approve" data-index="${index}">${esc(__('Approve'))}</button> <button class="btn btn-default review-return" data-index="${index}">${esc(__('Return for Correction'))}</button></p>`;
            html += `<button class="btn btn-default review-history" data-index="${index}">${esc(__('Review History'))}</button></details>`;
        }
                target.html(html);
        const act = (log, action, reason='') => frappe.call({method:'rpm_worklog.review.transition',type:'POST',
            args:{name:log.name,action,reason,expected_modified:log.modified}}).then(() => load_team(frm,from_date,to_date));
        target.find('.review-approve').on('click', function() {
            const log=data.logs[Number(this.dataset.index)];
            frappe.confirm(__('Approve this work log?'), () => act(log,'approve'));
        });
        target.find('.review-return').on('click', function() {
            const log=data.logs[Number(this.dataset.index)];
            frappe.prompt({fieldname:'reason',label:__('Return Reason'),fieldtype:'Small Text',reqd:1}, values => act(log,'return',values.reason), __('Return for Correction'));
        });
        target.find('.review-history').on('click', function() {
            const log=data.logs[Number(this.dataset.index)];
            frappe.call('rpm_worklog.review.history',{name:log.name}).then(r => frappe.msgprint({title:__('Review History'),message:r.message.map(e => `<p>${esc(e.event_time)} | ${esc(e.actor)} | ${esc(__(e.from_state))} → ${esc(__(e.to_state))}<br>${esc(e.reason)}</p>`).join('') || __('No review history')}));
        });
    }).catch(() => target.empty().text('查詢失敗，請查看錯誤訊息後重試。'));
}
