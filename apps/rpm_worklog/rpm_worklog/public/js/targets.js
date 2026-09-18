frappe.ui.form.on('RPM Daily Work Log', {
    setup(frm) {
        frm.set_query('work_target', 'lines', () => ({
            filters: {owner: frappe.session.user, status: 'Open'}
        }));
    },
    refresh(frm) {
        frm.set_df_property('lines', 'description', '跨日目標為選填，請逐列選取；未關聯的工作列不會計入目標彙整，相同工作內容也不會自動關聯。');
    }
});
