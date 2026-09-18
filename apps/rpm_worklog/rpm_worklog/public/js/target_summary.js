frappe.ui.form.on('RPM Work Target', {
    refresh(frm) {
        const wrapper = frm.fields_dict.work_summary.$wrapper;
        if (frm.is_new()) {
            wrapper.text('請先保存目標，再於工作紀錄的工作列關聯此目標。');
            return;
        }
        load_target_summary(frm, 0);
    }
});

function load_target_summary(frm, offset) {
    const wrapper = frm.fields_dict.work_summary.$wrapper;
    const name = frm.doc.name;
    const sequence = frm._target_summary_sequence = (frm._target_summary_sequence || 0) + 1;
    const current = () => frm.doc.name === name && frm._target_summary_sequence === sequence;
    wrapper.text('正在讀取已保存的工作紀錄…');
    frappe.call('rpm_worklog.targets.summary', {name, offset}).then(r => {
        if (!current()) return;
        const data = r.message;
        const esc = value => frappe.utils.escape_html(String(value ?? ''));
        const hours = value => Number(value || 0).toFixed(3);
        const labels = {'Draft':'草稿', 'Pending Review':'待審', 'Returned':'退回', 'Approved':'已核准', 'Other':'其他狀態'};
        const pending = Number(data.total_hours) - Number(data.totals.Approved.hours);
        let html = `<p>${esc(data.employee_label)}｜全部日期・已保存資料</p>
            <p><strong>累計 ${hours(data.total_hours)} 小時</strong>　已核准 ${hours(data.totals.Approved.hours)} 小時　尚未核准 ${hours(pending)} 小時</p>
            <p class="text-muted">僅加總關聯本目標的工作列，不含同張單的其他工作列或未保存修改。審核狀態依整張工作紀錄；工時不代表完成數量或完成率。更新其他頁面後，請按「重新整理工時」。</p>
            <button type="button" class="btn btn-default target-reload">重新整理工時</button>
            <div class="table-responsive" style="margin-top:12px"><table class="table table-bordered"><thead><tr><th>審核狀態</th><th>工時（小時）</th><th>工作列數</th></tr></thead><tbody>`;
        for (const state of Object.keys(labels)) {
            if (state === 'Other' && !data.totals.Other.entry_count) continue;
            html += `<tr><td>${labels[state]}</td><td>${hours(data.totals[state].hours)}</td><td>${data.totals[state].entry_count}</td></tr>`;
        }
        html += `</tbody></table></div><p>共 ${data.log_count} 張工作紀錄、${data.entry_count} 個關聯工作列。合計涵蓋全部資料，不受分頁影響。</p>`;
        if (!data.entry_count) {
            html += '<p>尚無關聯工作列。請在工作紀錄的工作列鉛筆明細中，選擇此跨日工作目標並保存。</p>';
        } else {
            html += '<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>日期</th><th>工作紀錄／列</th><th>作業類型</th><th>工作內容</th><th>結果</th><th>工時</th><th>審核狀態</th></tr></thead><tbody>';
            for (const row of data.rows) {
                const title = `${esc(row.title)}（${esc(row.work_log)}，第 ${esc(row.entry_index)} 列）`;
                const log = data.can_open_log ? `<a href="/desk/rpm-daily-work-log/${encodeURIComponent(row.work_log)}">${title}</a>` : `<button type="button" class="btn btn-link target-log-detail" data-log="${esc(row.work_log)}" style="white-space:normal;text-align:left">${title}（唯讀）</button>`;
                html += `<tr><td>${esc(row.work_date)}</td><td>${log}</td><td>${esc(row.activity_type)}</td><td>${esc(row.work_item)}</td><td>${esc(__(row.result))}</td><td>${hours(row.hours)}</td><td>${esc(labels[row.review_state] || row.review_state)}</td></tr>`;
            }
            html += '</tbody></table></div>';
            html += `<p>顯示 ${data.rows.length ? data.offset + 1 : 0}–${data.offset + data.rows.length} 列</p>`;
            if (data.offset > 0) html += '<button type="button" class="btn btn-default target-prev">上一頁</button> ';
            if (data.offset + data.rows.length < data.entry_count) html += '<button type="button" class="btn btn-default target-next">下一頁</button>';
        }
        wrapper.html(html);
        wrapper.find('.target-reload').on('click', () => load_target_summary(frm, 0));
        wrapper.find('.target-prev').on('click', () => load_target_summary(frm, Math.max(0, offset - 50)));
        wrapper.find('.target-next').on('click', () => load_target_summary(frm, offset + 50));
        wrapper.find('.target-log-detail').on('click', function() { open_target_worklog(name, this.dataset.log); });
    }).catch(() => {
        if (!current()) return;
        wrapper.empty().append($('<p>').text('無法讀取工時，請確認權限或稍後重試。'));
        $('<button type="button" class="btn btn-default">').text('重試').on('click', () => load_target_summary(frm, 0)).appendTo(wrapper);
    });
}

function open_target_worklog(name, work_log) {
    const dialog = new frappe.ui.Dialog({title:'工作紀錄（唯讀）',size:'extra-large',fields:[{fieldname:'detail',fieldtype:'HTML'}]});
    const wrapper = dialog.fields_dict.detail.$wrapper;
    wrapper.text('讀取中…');
    dialog.show();
    frappe.call('rpm_worklog.targets.worklog_detail', {name, work_log}).then(({message: data}) => {
        const esc = value => frappe.utils.escape_html(String(value ?? ''));
        const hours = value => Number(value || 0).toFixed(3);
        const states = {'Draft':'草稿','Pending Review':'待審','Returned':'退回','Approved':'已核准'};
        let html = `<p><strong>${esc(data.title)}</strong>（${esc(data.name)}）</p>
            <p>${esc(data.employee_label)}｜${esc(data.work_date)}｜${esc(states[data.review_state] || data.review_state)}</p>
            <p>整張紀錄：${hours(data.total_hours)} 小時。下表包含所有工作列，只有標示「本目標」的列計入剛才的目標彙整。</p>`;
        if (data.return_reason) html += `<p>退回原因：${esc(data.return_reason)}</p>`;
        html += '<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>列</th><th>關聯</th><th>作業類型</th><th>工作內容</th><th>數量</th><th>結果</th><th>開始／結束</th><th>工時</th><th>備註</th></tr></thead><tbody>';
        for (const row of data.lines) {
            html += `<tr><td>${esc(row.idx)}</td><td>${row.linked_to_target ? '本目標' : '其他工作列'}</td><td>${esc(row.activity_type)}</td><td>${esc(row.work_item)}</td><td>${esc(row.quantity)}</td><td>${esc(__(row.result))}</td><td>${esc(row.start_time)} / ${esc(row.end_time)}</td><td>${hours(row.hours)}</td><td>${esc(row.note)}</td></tr>`;
        }
        wrapper.html(html + '</tbody></table></div><p class="text-muted">此處僅供檢視；審核請使用「直屬員工工作紀錄」。關閉此視窗即可返回目標。</p>');
    }).catch(() => wrapper.text('無法讀取，關聯或權限可能已變動；請關閉視窗並重新整理目標頁。'));
}
