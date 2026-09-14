frappe.ui.form.on('RPM Work Log Analytics', {
    refresh(frm) {
        frm.disable_save();
        frm.doc.__unsaved = 0;
        frm.page.set_indicator(__('Read Only'), 'blue');
        const w = frm.fields_dict.results.$wrapper;
        const esc = x => frappe.utils.escape_html(String(x ?? ''));
        w.html(`<a href="/desk" class="btn btn-default">${__('Back to Home')}</a>
            <p>${__('Reports use the selected dates and review status. Quantity is not aggregated.')}</p>
            <div class="analytics-controls"></div><button class="btn btn-primary analytics-run">${__('Run Report')}</button>
            <div class="analytics-output" aria-live="polite"></div>`);
        const controls = {};
        const add = (fieldname, label, fieldtype, options) => {
            controls[fieldname] = frappe.ui.form.make_control({parent:w.find('.analytics-controls'), df:{fieldname,label:__(label),fieldtype,options}, render_input:true});
            return controls[fieldname];
        };
        const output = w.find('.analytics-output');
        const run = async () => {
            const args = Object.fromEntries(Object.entries(controls).map(([k,c]) => [k,c.get_value()]));
            if (!args.report || !args.from_date || !args.to_date) { frappe.msgprint(__('Select a report and date range')); return; }
            const button = w.find('.analytics-run').prop('disabled', true);
            output.empty().text(__('Loading...'));
            try {
                const {message:d} = await frappe.call('rpm_worklog.reports.run', args);
                const countUnit = d.grain === 'Log' ? __('Work Logs') : __('Work Entries');
                const unit = d.operation === 'Count' ? countUnit : __('Hours');
                const metric = `${__(d.operation)} (${unit})`;
                output.html(`<h3>${esc(__(d.title))}</h3><p>${esc(__(d.scope))} · ${esc(d.from_date)} ~ ${esc(d.to_date)} · ${esc(__(d.state))}<br>${esc(countUnit)}: ${d.sample_count} · ${esc(metric)}</p><div class="analytics-chart"></div><div class="table-responsive"><table class="table table-bordered"><thead><tr><th>${esc(d.group_label)}</th><th>${esc(metric)}</th></tr></thead><tbody></tbody></table></div>`);
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
                output.empty().text(__('Report failed. Check the error message and settings.'));
            } finally { button.prop('disabled', false); }
        };
        frappe.call('rpm_worklog.reports.options').then(({message:d}) => {
            add('report','Report','Select',d.reports.map(r => ({value:r.name,label:__(r.report_title)})));
            add('scope','Scope','Select',d.scopes.map(s => ({value:s,label:__(s)})));
            add('from_date','From Date','Date').set_value(frappe.datetime.month_start());
            add('to_date','To Date','Date').set_value(frappe.datetime.get_today());
            add('state','Review Status','Select',['All','Draft','Pending Review','Returned','Approved'].map(s => ({value:s,label:__(s)})));
            const defaults = () => controls.state.set_value(d.reports.find(r => r.name === controls.report.get_value())?.default_state || 'All');
            controls.report.df.onchange = defaults;
            defaults();
            w.find('.analytics-run').on('click',run);
        }).catch(() => output.text(__('Not permitted')));
        if (frappe.user.has_role('System Manager')) frm.add_custom_button(__('Report Settings'), () => frappe.set_route('List','RPM Work Log Report'));
    }
});
