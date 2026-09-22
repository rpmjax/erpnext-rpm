// Small screens use cards; native row forms keep validation and link controls intact.
frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) {
        const grid = frm.fields_dict.lines.grid;
        const wrapper = grid.wrapper;
        if (!frm.rpm_mobile_cards) {
            frm.rpm_mobile_cards = $('<div class="rpm-mobile-work-cards">').insertBefore(wrapper);
            const render = () => rpm_render_mobile_cards(frm);
            $(frm.wrapper).on('grid-row-render.rpmMobileCards', render);
            frm.rpm_mobile_observer = new MutationObserver(() => {
                clearTimeout(frm.rpm_mobile_timer);
                frm.rpm_mobile_timer = setTimeout(render, 50);
            });
            frm.rpm_mobile_observer.observe(wrapper[0], {childList:true,subtree:true,characterData:true});
        }
        wrapper.addClass('rpm-desktop-work-grid');
        if (!document.getElementById('rpm-mobile-work-style')) {
            $('<style id="rpm-mobile-work-style">').text(`
                .rpm-mobile-work-cards {display:none}
                @media(max-width:600px) {
                    .rpm-mobile-work-cards {display:block}
                    .rpm-desktop-work-grid .grid-heading-row,
                    .rpm-desktop-work-grid .grid-body .data-row,
                    .rpm-desktop-work-grid .grid-empty,
                    .rpm-desktop-work-grid > .grid-footer {display:none!important}
                    .rpm-mobile-work-card {border:1px solid var(--border-color,#ddd);border-radius:10px;padding:14px;margin:10px 0;overflow-wrap:anywhere}
                    .rpm-mobile-work-card dl {margin:10px 0}
                    .rpm-mobile-work-card dt {font-size:12px;color:var(--text-muted)}
                    .rpm-mobile-work-card dd {margin:2px 0 10px;white-space:pre-wrap}
                    .rpm-mobile-work-card button {min-height:44px}
                }`).appendTo(document.head);
        }
        rpm_render_mobile_cards(frm);
    }
});
function rpm_render_mobile_cards(frm) {
    const area=frm.rpm_mobile_cards;
    if (!area) return;
    const locked=['Pending Review','Approved'].includes(frm.doc.review_state) || !frm.perm?.[0]?.write;
    const esc=x=>frappe.utils.escape_html(String(x ?? ''));
    const grid=frm.fields_dict.lines.grid;
    area.empty();
    $('<p class="text-muted">').text('每張卡片是一筆工作；點「編輯工作」開啟垂直欄位。').appendTo(area);
    for (const row of frm.doc.lines || []) {
        const card=$('<section class="rpm-mobile-work-card">').appendTo(area);
        const pairs=[['作業類型',row.activity_type],['工作內容／物料',row.work_item],['跨日目標',row.work_target],['完成數量',row.quantity],['結果',__(row.result || '')],['工時',row.hours],['備註',row.note]];
        card.html(`<strong>第 ${esc(row.idx)} 筆工作</strong><dl>${pairs.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v === undefined || v === null || v === '' ? '—' : v)}</dd>`).join('')}</dl>`);
        $('<button type="button" class="btn btn-default">').text(locked?'查看明細':'編輯工作').appendTo(card).on('click',()=> {
            frm.rpm_material_row=row.name;
            grid.grid_rows_by_docname[row.name]?.toggle_view(true);
        });
    }
    if (!locked) $('<button type="button" class="btn btn-primary">').text('新增工作').appendTo(area).on('click',()=>{
        const row=frm.add_child('lines');
        frm.dirty(); frm.refresh_field('lines');
        frm.rpm_material_row=row.name;
        grid.grid_rows_by_docname[row.name]?.toggle_view(true);
    });
}
