frappe.ui.form.on('RPM Daily Work Log', {
    setup(frm) {
        frm.set_query('work_target', 'lines', () => ({
            filters: {owner: frappe.session.user, status: 'Open'}
        }));
    },
    refresh(frm) {
        frm.set_df_property('lines', 'description', '跨日目標為選填，請逐列選取；未關聯的工作列不會計入目標彙整，相同工作內容也不會自動關聯。');
        rpm_target_navigation(frm);
    }
});
frappe.ui.form.on('RPM Work Log Line', {
    work_target(frm) { rpm_target_navigation(frm); },
    lines_remove(frm) { rpm_target_navigation(frm); }
});

async function rpm_target_navigation(frm) {
    const field = frm.fields_dict.target_navigation;
    if (!field) return;
    const request = frm._target_nav_request = (frm._target_nav_request || 0) + 1;
    const docname = frm.doc.name;
    const current = () => request === frm._target_nav_request && docname === frm.doc.name;
    const names = [...new Set((frm.doc.lines || []).map(row => row.work_target).filter(Boolean))];
    const wrapper = field.$wrapper.empty();
    if (!names.length) {
        wrapper.append($('<p class="text-muted">').text('尚未關聯跨日目標；選取後，這裡會顯示快速入口。'));
        return;
    }
    wrapper.text('讀取關聯目標…');
    try {
        const {message: rows} = await frappe.call('frappe.client.get_list', {
            doctype: 'RPM Work Target', fields: ['name', 'target_name'],
            filters: [['name', 'in', names]], limit_page_length: names.length
        });
        if (!current()) return;
        wrapper.empty().append($('<label class="control-label">').text('前往關聯目標'));
        const links = $('<div>').appendTo(wrapper);
        for (const row of rows || []) {
            $('<a class="btn btn-default" target="_blank" rel="noopener noreferrer">')
                .attr('href', '/desk/rpm-work-target/' + encodeURIComponent(row.name))
                .css({marginRight: '8px', marginBottom: '8px', whiteSpace: 'normal'})
                .text(`${row.target_name}（${row.name}）`).appendTo(links);
        }
        if (!rows?.length) links.text('目前沒有可存取的關聯目標。');
        wrapper.append($('<p class="text-muted">').text('以新分頁開啟，保留此頁輸入；目標彙整僅包含已保存的工作列。'));
    } catch (error) {
        if (current()) wrapper.text('無法讀取關聯目標，請重新載入後重試。');
    }
}
