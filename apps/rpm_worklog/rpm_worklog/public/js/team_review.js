frappe.ui.form.on('RPM Team Work Log Viewer', {
    refresh(frm) {
        frm.add_custom_button(__('Work Log Analytics'), () => frappe.set_route('Form', 'RPM Work Log Analytics', 'RPM Work Log Analytics'));
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
    frappe.call('rpm_worklog.queries.team_summary', {from_date, to_date}).then(r => {
        const data = r.message;
        const esc = value => frappe.utils.escape_html(String(value ?? ''));
        const states = {'Draft':['草稿','draft'], 'Pending Review':['待審','pending'], 'Returned':['退回','returned'], 'Approved':['已核准','approved']};
        const hours = value => Number(value || 0).toFixed(3);
        let html = `<style>
            .rpm-team-card {border:1px solid var(--border-color,#dfe3e8);border-radius:12px;margin:0 0 14px;background:var(--card-bg,#fff);overflow:hidden;color:var(--text-color,#243247)}
            .rpm-team-card > summary {list-style:none;cursor:pointer;padding:16px;display:block}
            .rpm-team-card > summary::-webkit-details-marker {display:none}
            .rpm-team-card > summary:hover {background:var(--subtle-fg,#f6f8fa)}
            .rpm-team-card > summary:focus-visible {outline:2px solid var(--primary,#1677d2);outline-offset:-3px}
            .rpm-team-card .rpm-team-top {display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
            .rpm-team-card .rpm-team-person {font-size:15px;font-weight:600;overflow-wrap:anywhere}
            .rpm-team-card .rpm-team-title {font-size:16px;font-weight:600;line-height:1.5;margin-bottom:8px;overflow-wrap:anywhere}
            .rpm-team-card .rpm-team-meta {display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--text-muted,#667085);font-size:12px;overflow-wrap:anywhere}
            .rpm-team-card .rpm-team-bottom {display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-top:12px}
            .rpm-team-card .rpm-team-hours {font-size:18px;font-weight:600;font-variant-numeric:tabular-nums}
            .rpm-team-card .rpm-team-hours small {font-size:12px;font-weight:400;color:var(--text-muted,#667085)}
            .rpm-team-card .rpm-team-state {border-radius:16px;padding:3px 10px;font-size:12px;font-weight:600;white-space:nowrap}
            .rpm-team-card .rpm-state-draft {background:#eef0f3;color:#465365}
            .rpm-team-card .rpm-state-pending {background:#fff2cb;color:#795300}
            .rpm-team-card .rpm-state-returned {background:#ffe6df;color:#983d22}
            .rpm-team-card .rpm-state-approved {background:#def3e7;color:#22613f}
            .rpm-team-card .rpm-team-toggle {font-size:12px;color:var(--primary,#1677d2)}
            .rpm-team-card .rpm-team-close {display:none}
            .rpm-team-card[open] .rpm-team-close {display:inline}
            .rpm-team-card[open] .rpm-team-open {display:none}
            .rpm-team-card .rpm-team-body {padding:16px;border-top:1px solid var(--border-color,#dfe3e8)}
            .rpm-team-card table {margin-bottom:12px;min-width:540px}
            .rpm-team-card th {white-space:nowrap;background:var(--subtle-fg,#f6f8fa)}
            .rpm-team-card td {overflow-wrap:anywhere}
            .rpm-team-card .rpm-number {text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
            .rpm-team-card .rpm-team-actions {display:flex;flex-wrap:wrap;gap:8px}
            </style><p class="text-muted">${esc(from_date)} ～ ${esc(to_date)}<br>有效直屬員工 ${data.direct_report_count} 位 · 本次顯示 ${data.logs.length} 張</p>
            ${data.truncated ? '<p class="alert alert-warning">結果超過 300 張，請縮小日期範圍。</p>' : ''}
            ${!data.logs.length ? '<p class="alert alert-info">此日期範圍尚無直屬員工工作紀錄。</p>' : ''}`;
        for (const log of data.logs) {
            const [stateLabel, stateClass] = states[log.review_state || 'Draft'] || [log.review_state,'draft'];
            html += `<details class="rpm-team-card"><summary>
                <div class="rpm-team-top"><span class="rpm-team-person">${esc(log.employee_label || log.employee_name)}</span><span class="rpm-team-state rpm-state-${stateClass}">${esc(stateLabel)}</span></div>
                <div class="rpm-team-title">${esc(log.title)}</div>
                <div class="rpm-team-meta"><span>日期 ${esc(log.work_date)}</span><span>${esc(log.department)}</span><span>編號 ${esc(log.name)}</span></div>
                <div class="rpm-team-bottom"><span class="rpm-team-hours">${hours(log.total_hours)} <small>小時 · ${log.lines.length} 個工作列</small></span><span class="rpm-team-toggle"><span class="rpm-team-open">展開工作明細 ▾</span><span class="rpm-team-close">收合明細 ▴</span></span></div>
                </summary><div class="rpm-team-body"><div class="table-responsive"><table class="table table-bordered"><thead><tr><th scope="col">分類</th><th scope="col">工作內容／物料</th><th scope="col">數量</th><th scope="col">結果</th><th scope="col">工時</th><th scope="col">備註</th></tr></thead><tbody>`;
            for (const row of log.lines) html += `<tr><td>${esc(row.activity_type)}</td><td>${esc(row.work_item || [row.item_code,row.item_name_snapshot].filter(Boolean).join(" | "))}</td><td class="rpm-number">${esc(row.quantity)}</td><td>${esc(__(row.result))}</td><td class="rpm-number">${hours(row.hours)}</td><td>${esc(row.note)}</td></tr>`;
            html += '</tbody></table></div><div class="rpm-team-actions">';
            const index = data.logs.indexOf(log);
            if (log.review_state === 'Pending Review') html += `<button class="btn btn-primary review-approve" data-index="${index}">${esc(__('Approve'))}</button> <button class="btn btn-default review-return" data-index="${index}">${esc(__('Return for Correction'))}</button>`;
            html += `<button class="btn btn-default review-history" data-index="${index}">${esc(__('Review History'))}</button></div></div></details>`;
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
