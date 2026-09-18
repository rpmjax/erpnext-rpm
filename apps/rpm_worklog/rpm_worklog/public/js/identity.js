frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) { rpm_display_identity(frm); },
    employee(frm) { rpm_display_identity(frm); }
});
async function rpm_display_identity(frm) {
    const field = frm.fields_dict.employee_display;
    if (!field) return;
    const request = (frm.rpm_identity_request || 0) + 1;
    frm.rpm_identity_request = request;
    const name = frm.doc.name, employee = frm.doc.employee;
    const method = frm.is_new() ? 'rpm_worklog.queries.defaults' : 'rpm_worklog.queries.worklog_identity';
    try {
        const {message:d} = await frappe.call(method, frm.is_new() ? {} : {name});
        if (request !== frm.rpm_identity_request || name !== frm.doc.name || employee !== frm.doc.employee) return;
        if (!d || (d.employee || d.name) !== employee) return;
        field.$wrapper.empty().append($('<label class="control-label">').text('員工'))
            .append($('<div class="control-value like-disabled-input">').text(d.display_label));
        frm.set_df_property('employee','hidden',1);
        frm.set_df_property('employee_name','hidden',1);
    } catch (e) {
        field.$wrapper.empty();
        frm.set_df_property('employee','hidden',0);
        frm.set_df_property('employee_name','hidden',0);
    }
}
