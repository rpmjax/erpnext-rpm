frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) {
        const page = $(frm.page.wrapper);
        const personal = frm.is_new() || frm.doc.owner === frappe.session.user;
        page.toggleClass('rpm-personal-worklog', personal);
        // A different document starts collapsed; refreshes preserve the user's choice.
        if (frm.rpm_details_doc !== frm.doc.name) {
            frm.rpm_details_doc = frm.doc.name;
            frm.rpm_details_open = false;
        }
        page.toggleClass('rpm-details-collapsed', personal && !frm.rpm_details_open);
        if (!document.getElementById('rpm-personal-sidebar-style')) {
            $('<style id="rpm-personal-sidebar-style">').text(`
                .rpm-personal-worklog.rpm-details-collapsed .layout-side-section.right {display:none!important}
                .rpm-personal-worklog.rpm-details-collapsed .layout-main-section-wrapper {width:100%!important;max-width:100%!important;flex:1 1 100%!important}
            `).appendTo(document.head);
        }
        if (personal) {
            const button = frm.add_custom_button('附件／紀錄資訊', () => {
                frm.rpm_details_open = !frm.rpm_details_open;
                page.toggleClass('rpm-details-collapsed', !frm.rpm_details_open);
                button.attr('aria-expanded', String(frm.rpm_details_open));
            });
            button.attr('aria-expanded', String(!!frm.rpm_details_open));
        }
    }
});
