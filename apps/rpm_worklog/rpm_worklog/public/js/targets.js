frappe.ui.form.on('RPM Daily Work Log', {
    setup(frm) {
        frm.set_query('work_target', 'lines', () => ({
            filters: {owner: frappe.session.user, status: 'Open'}
        }));
    }
});
