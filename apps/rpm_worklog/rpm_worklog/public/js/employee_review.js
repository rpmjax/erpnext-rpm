frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) {
        const state = frm.doc.review_state || 'Draft';
        const locked = ['Pending Review', 'Approved'].includes(state);
        ['title','work_date','lines'].forEach(field => frm.set_df_property(field, 'read_only', locked ? 1 : 0));
        if (locked) frm.disable_save(); else frm.enable_save();
        frm.page.clear_secondary_action();
        if (frm.is_new()) return;
        if (['Draft','Returned'].includes(state)) frm.page.set_secondary_action(__('Send for Review'), () => {
            if (frm.is_dirty()) { frappe.msgprint(__('Save changes before sending for review')); return; }
            frappe.confirm(__('Send this work log for review?'), () => frappe.call({
                method:'rpm_worklog.review.transition', type:'POST',
                args:{name:frm.doc.name,action:'submit',expected_modified:frm.doc.modified},
                callback:() => frm.reload_doc()
            }));
        });
        frm.add_custom_button(__('Review History'), () => {
            frappe.call('rpm_worklog.review.history', {name:frm.doc.name}).then(r => {
                const esc = x => frappe.utils.escape_html(String(x ?? ''));
                frappe.msgprint({title:__('Review History'), message:r.message.map(e =>
                    `<p>${esc(e.event_time)} | ${esc(e.actor)} | ${esc(__(e.from_state))} → ${esc(__(e.to_state))}<br>${esc(e.reason)}</p>`).join('') || __('No review history')});
            });
        });
    }
});
