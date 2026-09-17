frappe.ui.form.on('RPM Work Log Access', {
    refresh(frm) {
        frm.disable_save();
        frm.doc.__unsaved = 0;
        frm.page.set_indicator('管理操作', 'blue');
        const w = frm.fields_dict.controls.$wrapper.empty();
        const esc = v => frappe.utils.escape_html(String(v ?? ''));
        w.html(`<style>.rpm-access-table {min-width:950px} .rpm-access-table th {white-space:nowrap} .rpm-access-table td {vertical-align:top} .rpm-access-table td:last-child {min-width:280px}</style><a href="/desk" class="btn btn-default">返回首頁</a>
            <h3>工作紀錄開通管理</h3><p>僅授予工作紀錄角色；不建立帳號、不重設密碼。主管若也需填寫本人紀錄，請另外開通員工角色。</p>
            <input class="form-control search" aria-label="搜尋帳號" placeholder="Email、姓名或登入帳號">
            <button class="btn btn-default query">查詢</button>
            <button class="btn btn-default select-all">選取可開通者</button>
            <button class="btn btn-primary employee">開通員工</button>
            <button class="btn btn-default manager">開通主管</button>
            <p class="hint" aria-live="polite"></p><div class="table-responsive records"></div>
            <div class="result" aria-live="polite"></div>`);
        let rows = [], busy = false;
        const load = async () => {
            if (busy) return;
            busy = true; w.find('button').prop('disabled', true);
            try {
                const {message:d} = await frappe.call('rpm_worklog.access.users', {text:w.find('.search').val()});
                rows = d.users;
                w.find('.hint').text(d.has_more ? '僅顯示前 50 人，請縮小搜尋條件。' : `共 ${rows.length} 人。操作後請使用者登出再登入。`);
                w.find('.records').html(`<table class="table table-bordered rpm-access-table"><thead><tr><th>選取</th><th>User</th><th>工號｜姓名</th><th>員工角色</th><th>主管角色</th><th>檢查</th></tr></thead><tbody>${rows.map((r,i) => `<tr><td><input type="checkbox" aria-label="選取 ${esc(r.user)}" data-index="${i}" ${r.reasons.length ? 'disabled' : ''}></td><td>${esc(r.user)}<br>${esc(r.full_name)}</td><td>${esc(r.employee_label)}</td><td>${r.employee_role ? '有' : '未開通'}</td><td>${r.manager_role ? '有' : '未開通'}</td><td>${esc(r.reasons.join('；') || (r.adjustments?.length ? '需確認調整：' + r.adjustments.join('；') : '') || (r.ready ? '本人權限已配置' : '可開通／補齊本人權限'))}</td></tr>`).join('')}</tbody></table>`);
            } catch (e) { rows = []; w.find('.records').empty(); w.find('.hint').text('查詢失敗，請確認管理員權限。'); }
            finally { busy = false; w.find('button').prop('disabled', false); }
        };
        const enroll = mode => {
            const users = w.find('input[data-index]:checked').map((_,el) => rows[Number(el.dataset.index)].user).get();
            if (!users.length || busy) return frappe.msgprint('請先選取使用者');
            const changes = rows.filter(r => users.includes(r.user) && r.adjustments?.length);
            const details = changes.length ? '<hr><b>同時調整既有本人 Employee User Permission：</b><ul>' + changes.map(r => '<li>' + esc(r.user) + '：' + esc(r.adjustments.join('；')) + '</li>').join('') + '</ul><p>套用至所有文件及排除下屬會影響其他 ERPNext 功能的 Employee 存取範圍；不修改指向其他員工的權限。</p>' : '';
            frappe.confirm(`將為 ${users.length} 人開通${mode === 'manager' ? '主管（可查看及審核直屬員工）' : '員工（填寫本人紀錄）'}權限，是否繼續？${details}`, async () => {
                if (busy) return;
                busy = true; w.find('button').prop('disabled', true);
                try {
                    const {message:results} = await frappe.call({method:'rpm_worklog.access.enroll', type:'POST', args:{users,mode,normalize_own:changes.length ? 1 : 0}});
                    const labels = {enrolled:'開通完成', unchanged:'已配置，無需變更', failed:'未開通'};
                    w.find('.result').html('<h4>處理結果</h4>' + results.map(r => `<p>${esc(r.user)}：${labels[r.status]} ${esc(r.reason || '')}</p>`).join(''));
                } catch (e) { w.find('.result').text('操作失敗，本次請求未完成；請查看錯誤訊息並重新查詢。'); }
                finally { busy = false; await load(); }
            });
        };
        w.find('.query').on('click', load);
        w.find('.search').on('keydown', e => { if (e.key === 'Enter') load(); });
        w.find('.select-all').on('click', () => w.find('input[data-index]:enabled').prop('checked', true));
        w.find('.employee').on('click', () => enroll('employee'));
        w.find('.manager').on('click', () => enroll('manager'));
        load();
    }
});
