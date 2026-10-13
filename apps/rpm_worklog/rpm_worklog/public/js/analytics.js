frappe.ui.form.on('RPM Work Log Analytics', {
    refresh(frm) {
        frm.disable_save();
        frm.doc.__unsaved = 0;
        frm.page.set_indicator(__('Read Only'), 'blue');
        const w = frm.fields_dict.results.$wrapper;
        frm.add_custom_button('工作明細分析／匯出', () => rpm_worklog_analysis_open());
        if (frappe.session.user === 'Administrator' || frappe.user.has_role('System Manager')) {
            frm.add_custom_button('Worklog 設定', () => frappe.set_route('Form','RPM Worklog Settings','RPM Worklog Settings'));
        }
        const scopeLabels = {Self:'本人',Team:'有效直屬員工',Organization:'公司全員（含離職歷史）'};
        const esc = x => frappe.utils.escape_html(String(x ?? ''));
        w.html(`<a href="/desk" class="btn btn-default">${__('Back to Home')}</a>
            <p>${__('Reports use the selected dates and review status. Quantity is not aggregated.')}</p>
            <div class="analytics-controls"></div><button class="btn btn-primary analytics-run">${__('Run Report')}</button>
            <div class="analytics-output" aria-live="polite"></div>`);
        const controls = {};
        const distribution = 'rpm-employee-work-time-distribution';
        const isDistribution = () => controls.report?.get_value() === distribution;
        const add = (fieldname, label, fieldtype, options) => {
            controls[fieldname] = frappe.ui.form.make_control({parent:w.find('.analytics-controls'), df:{fieldname,label:__(label),fieldtype,options}, render_input:true});
            return controls[fieldname];
        };
        const output = w.find('.analytics-output');
        let selectedEmployee = '', selectedLabel = '', searchVersion = 0, queryVersion = 0;
        const invalidate = () => { ++queryVersion; output.empty(); };
        const run = async () => {
            const args = Object.fromEntries(Object.entries(controls).map(([k,c]) => [k,c.get_value()]));
            args.employee = selectedEmployee;
            delete args.period;
            delete args.anchor;
            if (!args.report || !args.from_date || !args.to_date) { frappe.msgprint(__('Select a report and date range')); return; }
            if (isDistribution() && args.scope !== 'Self' && !selectedEmployee) {
                output.empty().text('請搜尋並選擇一名員工。'); return;
            }
            const ticket = ++queryVersion;
            const button = w.find('.analytics-run').prop('disabled', true);
            output.empty().text(__('Loading...'));
            try {
                const special = isDistribution();
                if (special) delete args.report;
                const {message:d} = await frappe.call(special ? 'rpm_worklog.activity_distribution.query' : 'rpm_worklog.reports.run', args);
                if (ticket !== queryVersion || !w[0].isConnected) return;
                if (special) { rpm_render_distribution(output, d); return; }
                const countUnit = d.grain === 'Log' ? __('Work Logs') : __('Work Entries');
                const unit = d.operation === 'Count' ? countUnit : __('Hours');
                const metric = `${__(d.operation)} (${unit})`;
                output.html(`<h3>${esc(__(d.title))}</h3><p>${esc(scopeLabels[d.scope] || d.scope)} · ${esc(d.from_date)} ~ ${esc(d.to_date)} · ${esc(__(d.state))}<br>${esc(countUnit)}: ${d.sample_count} · ${esc(metric)}</p><div class="analytics-chart"></div><div class="table-responsive"><table class="table table-bordered"><thead><tr><th>${esc(d.group_label)}</th><th>${esc(metric)}</th></tr></thead><tbody></tbody></table></div>`);
                if (d.employee_label) output.find('h3').after($('<p>').text(d.employee_label));
                const body = output.find('tbody');
                d.rows.forEach(r => body.append(`<tr><td>${esc(__(r.label))}</td><td>${esc(Number(r.value).toFixed(d.operation === 'Count' ? 0 : 3))}</td></tr>`));
                if (!d.rows.length) { output.append($('<p>').text(__('No data in this scope'))); return; }
                if (d.rows.length > 60) { output.prepend($('<p>').text(__('More than 60 groups: showing the complete table only. Narrow dates for a chart.'))); return; }
                if (!frappe.Chart) { output.prepend(document.createTextNode(__('Chart unavailable; complete table shown.'))); return; }
                new frappe.Chart(output.find('.analytics-chart')[0], {
                    type:d.chart_type, height:300,
                    data:{labels:d.rows.map(r => __(r.label)), datasets:[{name:metric,values:d.rows.map(r => r.value)}]}
                });
            } catch (e) {
                if (ticket !== queryVersion) return;
                output.empty().text(__('Report failed. Check the error message and settings.'));
            } finally { button.prop('disabled', false); }
        };
        frappe.call('rpm_worklog.reports.options').then(async ({message:d}) => {
            add('report','Report','Select',d.reports.map(r => ({value:r.name,label:__(r.report_title)})));
            await controls.report.set_value(distribution);
            add('scope','Scope','Select',d.scopes.map(s => ({value:s,label:scopeLabels[s] || __(s)})));
            await controls.scope.set_value(d.scopes.includes('Organization') ? 'Organization' : d.scopes[0]);
            if (d.company) w.find('.analytics-controls').prepend($('<p>').text('公司範圍：' + d.company));
            const picker = $('<div class="form-group">').appendTo(w.find('.analytics-controls'));
            const search = $('<input type="search" class="form-control" aria-label="工號或姓名" placeholder="輸入工號或姓名搜尋員工">').appendTo(picker);
            const listId = 'rpm-employees-' + Math.random().toString(36).slice(2);
            search.attr({role:'combobox','aria-autocomplete':'list','aria-expanded':'false','aria-controls':listId,autocomplete:'off'});
            const choices = $('<div role="listbox" aria-label="選擇員工">').attr('id',listId)
                .css({maxHeight:'220px',overflowY:'auto',border:'1px solid var(--border-color)',borderRadius:'6px'}).hide().appendTo(picker);
            let candidates = [], active = -1;
            const closeChoices = () => {
                choices.hide(); active = -1;
                search.attr('aria-expanded','false').removeAttr('aria-activedescendant');
            };
            const activate = index => {
                active = index;
                choices.children().each((i, el) => $(el).attr('aria-selected',String(i === active))
                    .css({background:i === active ? 'var(--control-bg)' : '',fontWeight:i === active ? '600' : ''}));
                if (active >= 0) {
                    search.attr('aria-activedescendant',listId+'-'+active);
                    choices.children()[active]?.scrollIntoView({block:'nearest'});
                }
            };
            const choose = index => {
                const candidate = candidates[index]; if (!candidate) return;
                ++searchVersion; clearTimeout(timer);
                selectedEmployee = candidate.value; selectedLabel = candidate.label;
                search.val(selectedLabel); closeChoices(); showSelection(); invalidate();
            };
            const hint = $('<p class="text-muted" aria-live="polite">').appendTo(picker);
            const clear = $('<button type="button" class="btn btn-default">目前範圍全部員工</button>').appendTo(picker);
            const showSelection = () => hint.text(selectedEmployee ? `已選：${selectedLabel}` :
                (isDistribution() ? '請選擇一名員工；候選依已有工作紀錄列出，不受日期限制。' : '目前範圍全部員工；候選依已有工作紀錄列出，不受日期限制。'));
            const searchEmployees = async () => {
                const version = ++searchVersion;
                choices.empty(); candidates = []; closeChoices();
                const selectedScope = controls.scope.get_value();
                if (selectedScope === 'Self') return;
                try {
                    const {message:result} = await frappe.call('rpm_worklog.reports.search_employees', {scope:selectedScope, text:search.val()});
                    if (version !== searchVersion || !picker[0].isConnected) return;
                    candidates = result.employees;
                    candidates.forEach((e,i) => $('<div role="option" aria-selected="false">')
                        .attr('id',listId+'-'+i).text(e.label).css({padding:'8px',cursor:'pointer'})
                        .on('mousedown',event => event.preventDefault())
                        .on('click',() => choose(i)).appendTo(choices));
                    if (candidates.length) { choices.show(); search.attr('aria-expanded','true'); }
                    showSelection();
                    if (result.has_more) hint.append(document.createTextNode(' 候選超過 20 人，請輸入更完整的工號或姓名。'));
                    else if (!result.employees.length) hint.append(document.createTextNode(' 無符合的員工。'));
                } catch (e) {
                    if (version === searchVersion) hint.text('搜尋失敗，請重新輸入並選取員工。');
                }
            };
            let timer;
            search.on('input', () => {
                ++searchVersion; clearTimeout(timer); candidates=[]; choices.empty(); closeChoices();
                selectedEmployee=''; selectedLabel=''; invalidate(); showSelection();
                timer = setTimeout(searchEmployees,250);
            });
            search.on('focus',() => { if (!selectedEmployee) searchEmployees(); });
            search.on('blur',() => { ++searchVersion; clearTimeout(timer); closeChoices(); });
            search.on('keydown',event => {
                if (event.isComposing || event.originalEvent?.isComposing) return;
                if (event.key === 'Escape') { ++searchVersion; clearTimeout(timer); closeChoices(); }
                else if (['ArrowDown','ArrowUp'].includes(event.key)) {
                    event.preventDefault();
                    if (!candidates.length) { searchEmployees(); return; }
                    choices.show(); search.attr('aria-expanded','true');
                    activate(rpm_candidate_index(active,event.key,candidates.length));
                } else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); choose(active); }
            });
            clear.on('click', () => { selectedEmployee = ''; selectedLabel = ''; search.val(''); invalidate(); searchEmployees(); });
            const scopeChanged = () => {
                ++searchVersion; clearTimeout(timer); selectedEmployee = ''; selectedLabel = ''; search.val(''); invalidate();
                picker.toggle(controls.scope.get_value() !== 'Self');
                searchEmployees();
            };
            controls.scope.df.onchange = scopeChanged;
            scopeChanged();
            add('from_date','From Date','Date').set_value(frappe.datetime.month_start());
            add('to_date','To Date','Date').set_value(frappe.datetime.get_today());
            add('state','Review Status','Select',['All','Draft','Pending Review','Returned','Approved'].map(s => ({value:s,label:__(s)})));
            add('period','統計期間','Select',['日','週','月','自訂']).set_value('自訂');
            add('anchor','基準日期','Date').set_value(frappe.datetime.get_today());
            let presetChanging = false;
            const applyPeriod = async () => {
                invalidate();
                const range = rpm_distribution_range(controls.period.get_value(), controls.anchor.get_value());
                if (!range) return;
                presetChanging = true;
                try {
                    await controls.from_date.set_value(range[0]);
                    await controls.to_date.set_value(range[1]);
                } finally { presetChanging = false; }
            };
            controls.period.df.onchange = applyPeriod;
            controls.anchor.df.onchange = applyPeriod;
            for (const key of ['from_date','to_date']) controls[key].df.onchange = () => {
                invalidate(); if (!presetChanging) controls.period.set_value('自訂');
            };
            controls.state.df.onchange = invalidate;
            const reportUI = () => {
                const special = isDistribution();
                $(controls.period.$wrapper).toggle(special);
                $(controls.anchor.$wrapper).toggle(special);
                clear.text(special ? '清除選取' : '目前範圍全部員工');
                showSelection();
            };
            const defaults = () => controls.state.set_value(d.reports.find(r => r.name === controls.report.get_value())?.default_state || 'All');
            controls.report.df.onchange = () => { invalidate(); defaults(); reportUI(); };
            defaults(); reportUI();
            w.find('.analytics-run').on('click',run);
        }).catch(() => output.text(__('Not permitted')));
        if (frappe.user.has_role('System Manager')) frm.add_custom_button(__('Report Settings'), () => frappe.set_route('List','RPM Work Log Report'));
    }
});

function rpm_candidate_index(index, key, length) {
    if (!length) return -1;
    return key === 'ArrowDown' ? (index + 1) % length : (index < 0 ? length - 1 : (index - 1 + length) % length);
}

function rpm_distribution_range(period, anchor) {
    if (period === '自訂' || !/^\d{4}-\d{2}-\d{2}$/.test(anchor || '')) return null;
    const d = new Date(anchor + 'T00:00:00Z');
    if (!Number.isFinite(d.getTime())) return null;
    const start = new Date(d), end = new Date(d);
    if (period === '週') {
        start.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7);
        end.setTime(start.getTime()); end.setUTCDate(start.getUTCDate() + 6);
    } else if (period === '月') {
        start.setUTCDate(1); end.setUTCMonth(end.getUTCMonth() + 1, 0);
    }
    return [start, end].map(x => x.toISOString().slice(0,10));
}

function rpm_render_distribution(output, d) {
    const esc = x => frappe.utils.escape_html(String(x ?? ''));
    const h = x => Number(x).toFixed(3);
    const itemLabel = x => x === null ? '（未填內容）' : x === '' ? '（空白內容）' : x;
    const tooltip = g => `${g.display_label}\n${h(g.hours)} 小時｜${g.percentage.toFixed(2)}%｜${g.line_count} 筆\n主要工作內容／物料\n` +
        g.top_items.map(x => `${itemLabel(x.work_item)}　${h(x.hours)} h`).join('\n') +
        (g.remaining.distinct_item_count ? `\n其他 ${g.remaining.distinct_item_count} 種內容，${g.remaining.line_count} 筆，共 ${h(g.remaining.hours)} h` : '');
    output.html(`<style>
        .rpm-distribution-slice {cursor:pointer;outline:none;}
        .rpm-distribution-slice[aria-expanded="true"] {stroke:var(--text-color,#222);stroke-width:2;stroke-linejoin:round;}
        .rpm-distribution-slice:focus-visible {stroke:var(--text-color,#222);stroke-width:4;stroke-dasharray:4 2;}
        </style><h3>員工工作時間分布</h3><p>${esc(d.employee.label)}<br>${esc(d.scope)} · ${esc(d.from_date)} ~ ${esc(d.to_date)} · ${esc(__(d.review_state))}</p>
        <p>申報總工時 ${h(d.totals.reported_hours)} 小時 · 工作列 ${d.totals.line_count} 筆 · 作業類型 ${d.totals.activity_type_count} 種 · 未分類 ${d.totals.unclassified_line_count} 筆</p>
        <p>自主申報工時分布，非績效或效率評分。展開明細可查看主要工作內容／物料。</p>`);
    if (!d.groups.length) { output.append($('<p>').text('無符合紀錄')); return; }
    const max = Math.max(...d.groups.map(g => g.hours), 0);
    const bars = $('<div aria-label="作業類型工時長條圖">').appendTo(output);
    const pie = $('<div>').appendTo(output);
    let angle = 0;
    const slices = [];
    const details = [];
    const chartId = 'rpm-distribution-' + Math.random().toString(36).slice(2);
    d.groups.forEach((g, i) => {
        const color = `hsl(${i * 137.508 % 360},55%,45%)`;
        $('<div tabindex="0">').attr('title',tooltip(g)).css({marginBottom:'8px'}).append(
            $('<div>').text(`${g.display_label} — ${h(g.hours)} h (${g.percentage.toFixed(2)}%)`),
            $('<div>').css({height:'16px',background:color,width:`${max ? Math.max(0,g.hours/max*100) : 0}%`})
        ).appendTo(bars);
        const fraction = d.totals.reported_hours > 0 ? g.hours / d.totals.reported_hours : 0;
        if (fraction > 0) {
            const next = angle + fraction * Math.PI * 2;
            const x = a => 100 + 90 * Math.cos(a), y = a => 100 + 90 * Math.sin(a);
            const shape = fraction >= 1 ? '<circle cx="100" cy="100" r="90"' :
                `<path d="M100 100 L${x(angle)} ${y(angle)} A90 90 0 ${fraction > .5 ? 1 : 0} 1 ${x(next)} ${y(next)} Z"`;
            slices.push(`${shape} class="rpm-distribution-slice" data-index="${i}" fill="${color}" tabindex="0" role="button" aria-expanded="false" aria-controls="${chartId}-${i}" aria-label="${esc(g.display_label)}：展開明細"><title>${esc(tooltip(g))}</title></${fraction >= 1 ? 'circle' : 'path'}>`);
            angle = next;
        }
        const detail = $('<details>').attr('id',chartId+'-'+i).appendTo(output);
        details.push(detail);
        $('<summary>').text(`${g.display_label}｜${h(g.hours)} 小時｜${g.percentage.toFixed(2)}%｜${g.line_count} 筆`).appendTo(detail);
        g.top_items.forEach(x => $('<p>').css('white-space','pre-wrap').text(`${itemLabel(x.work_item)} — ${h(x.hours)} h｜${x.line_count} 筆`).appendTo(detail));
        if (g.remaining.distinct_item_count) $('<p>').text(`其他 ${g.remaining.distinct_item_count} 種內容，${g.remaining.line_count} 筆，共 ${h(g.remaining.hours)} h`).appendTo(detail);
    });
    if (d.totals.reported_hours > 0) {
        pie.html(`<svg viewBox="0 0 200 200" style="width:240px;max-width:100%" role="group" aria-label="作業類型工時比例圓餅圖，點選展開明細">${slices.join('')}</svg>`);
        pie.find('.rpm-distribution-slice').each((_, element) => {
            const detail = details[Number(element.dataset.index)];
            const expand = () => { detail.prop('open',true); };
            $(element).on('click',expand).on('keydown',event => {
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); expand(); }
            });
            detail.on('toggle',() => $(element).attr('aria-expanded',String(detail.prop('open'))));
        });
    }
}
