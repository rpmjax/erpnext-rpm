frappe.listview_settings['RPM Daily Work Log'] = {
    add_fields: ['modified', 'review_state'],
    has_indicator_for_draft: true,
    get_indicator(doc) {
        const state = doc.review_state || 'Draft';
        const colors = {'Draft':'gray','Pending Review':'blue','Returned':'orange','Approved':'green'};
        const labels = {'Draft':'草稿','Pending Review':'待審','Returned':'退回修改','Approved':'已核准'};
        return [labels[state] || state, colors[state] || 'gray', `review_state,=,${state}`];
    },
    onload(listview) {
        listview.page.add_action_item(__('Send for Review'), () => {
            if (listview.rpm_submitting) return;
            const selected = listview.get_checked_items();
            if (!selected.length || selected.length > 50) { frappe.msgprint(__('Select between 1 and 50 work logs')); return; }
            const records = selected.map(row => ({name:row.name,modified:row.modified}));
            frappe.confirm(__('Send {0} selected work logs for review?', [records.length]), () => {
                if (listview.rpm_submitting) return;
                listview.rpm_submitting = true;
                frappe.call({method:'rpm_worklog.review.bulk_submit',type:'POST',args:{records:JSON.stringify(records)},freeze:true,freeze_message:__('Sending for review...')})
                .then(r => {
                    const data=r.message, esc=x=>frappe.utils.escape_html(String(x ?? ''));
                    const summary=__('Success: {0}; skipped: {1}; failed: {2}',[data.counts.success,data.counts.skipped,data.counts.failed]);
                    frappe.msgprint({title:__('Bulk Submission Results'),message:`<p>${esc(summary)}</p>` + data.results.map(row=>`<p>${esc(row.name)} | ${esc(__(row.status))} | ${esc(row.message)}</p>`).join('')});
                }).finally(() => { listview.rpm_submitting=false; listview.refresh(); });
            });
        });
    }
};
