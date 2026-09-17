frappe.ui.form.on('RPM Daily Work Log', {
    setup(frm) {
        frm.set_query('item_code', 'lines', () => ({query:'rpm_worklog.items.link_query'}));
        let sequence = 0, timer, menu;
        const close = () => { ++sequence; clearTimeout(timer); if (menu) menu.remove(); };
        $(frm.wrapper).on('input.rpmFreeItem', 'input[data-fieldname="work_item"]', function() {
            close();
            const input = this, text = input.value;
            const name = $(input).closest('.grid-row').attr('data-name');
            const row = (frm.doc.lines || []).find(r => r.name === name);
            if (!row || !text || ['Pending Review','Approved'].includes(frm.doc.review_state)) return;
            const request = sequence;
            timer = setTimeout(async () => {
                try {
                    const {message:items} = await frappe.call('rpm_worklog.items.search_items', {text});
                    if (request !== sequence || document.activeElement !== input) return;
                    const rect = input.getBoundingClientRect();
                    menu = $('<div role="listbox" class="dropdown-menu" style="display:block;position:fixed;z-index:2000;max-height:240px;overflow:auto">').css({top:rect.bottom,left:rect.left,width:Math.min(420,window.innerWidth-rect.left-12)}).appendTo(document.body);
                    $('<div class="text-muted" style="padding:8px">').text('可直接保留輸入文字；點選以下物料才建立關聯。').appendTo(menu);
                    items.forEach(item => $('<button type="button" class="dropdown-item" style="white-space:normal">').text(`${item.name} | ${item.item_name}`).appendTo(menu)
                        .on('mousedown', e => e.preventDefault()).on('click', async () => { close(); await rpm_choose_item(frm,row,item); frm.refresh_field('lines'); }));
                } catch (e) { close(); }
            },250);
        }).on('focusout.rpmFreeItem', 'input[data-fieldname="work_item"]', close);
    },
    refresh(frm) { rpm_material_toolbar(frm); }
});
function rpm_material_toolbar(frm) {
    const area = frm.fields_dict.work_entry_help.$wrapper;
    area.empty();
    $('<p>').text('「工作內容／物料」可自由填寫，例如跨部門協助；輸入 sho 可搜尋物料，點選候選才建立關聯。修改文字會解除原物料關聯。').appendTo(area);
    const rows = frm.doc.lines || [];
    if (!rows.length) { $('<p>').text('請先按「添加行」建立工作列。').appendTo(area); return; }
    const locked = ['Pending Review','Approved'].includes(frm.doc.review_state);
    if (locked) { $('<p>').text('目前紀錄已鎖定，不能變更物料關聯。').appendTo(area); return; }
    const label = $('<label>').text('操作工作列：').appendTo(area);
    const select = $('<select class="form-control" style="display:inline-block;width:auto;max-width:100%;margin:0 8px">').appendTo(label);
    rows.forEach(row => $('<option>').val(row.name).text(`第 ${row.idx} 列${row.item_code ? '｜' + row.item_code : '｜未關聯物料'}`).appendTo(select));
    if (rows.some(row => row.name === frm.rpm_material_row)) select.val(frm.rpm_material_row);
    select.on('change', () => { frm.rpm_material_row = select.val(); });
    const action = event => {
        const row = (frm.doc.lines || []).find(row => row.name === select.val());
        if (row) { frm.rpm_material_row = row.name; frm.script_manager.trigger(event,row.doctype,row.name); }
    };
    $('<button type="button" class="btn btn-primary" style="margin:4px">').text(__('Search Item')).appendTo(area).on('click', () => action('search_item'));
    $('<button type="button" class="btn btn-default" style="margin:4px">').text(__('Remove Item Link')).appendTo(area).on('click', () => action('clear_item'));
}
frappe.ui.form.on('RPM Work Log Line', {
    work_item(frm,cdt,cdn) {
        frappe.model.set_value(cdt,cdn,{item_code:'',item_name_snapshot:''});
    },
    lines_add(frm) { rpm_material_toolbar(frm); },
    lines_remove(frm) { rpm_material_toolbar(frm); },
    item_code(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, 'item_name_snapshot', ''); rpm_material_toolbar(frm); },
    search_item(frm, cdt, cdn) {
        if (['Pending Review','Approved'].includes(frm.doc.review_state)) return;
        const row = locals[cdt][cdn];
        const dialog = new frappe.ui.Dialog({title:__('Search Item'),fields:[
            {fieldname:'keyword',label:__('Item code or name'),fieldtype:'Data'},
            {fieldname:'matches',fieldtype:'HTML'}
        ]});
        let sequence = 0;
        const search = () => {
            const request = ++sequence;
            const area = dialog.fields_dict.matches.$wrapper;
            area.text(__('Searching...'));
            frappe.call('rpm_worklog.items.search_items',{text:dialog.get_value('keyword') || ''}).then(r => {
                if (request !== sequence) return;
                area.empty();
                $('<p>').text(__('Up to 20 results. Refine your search if needed.')).appendTo(area);
                if (!r.message.length) $('<p>').text(__('No matching items. You can still enter work content freely.')).appendTo(area);
                for (const item of r.message) {
                    $('<button type="button" class="btn btn-default" style="display:block;margin:6px 0;text-align:left;white-space:normal">')
                    .text(`${item.name} | ${item.item_name}`).appendTo(area).on('click', async () => {
                        await rpm_choose_item(frm,row,item);
                        dialog.hide(); frm.refresh_field('lines');
                    });
                }
            }).catch(() => { if (request === sequence) area.text(__('Search failed. Please try again.')); });
        };
        dialog.fields_dict.keyword.$input.on('input',frappe.utils.debounce(search,300));
        dialog.show(); search();
    },
    clear_item(frm,cdt,cdn) {
        if (['Pending Review','Approved'].includes(frm.doc.review_state)) return;
        frappe.model.set_value(cdt,cdn,{item_code:'',item_name_snapshot:'',item_stock_uom:'',item_conversion_factor:0});
        frappe.show_alert({message:__('Item link removed; work content and unit retained'),indicator:'blue'});
    }
});
async function rpm_choose_item(frm,row,item) {
    if (['Pending Review','Approved'].includes(frm.doc.review_state)) return;
    await frappe.model.set_value(row.doctype,row.name,'work_item',`${item.name} | ${item.item_name}`.slice(0,140));
    await frappe.model.set_value(row.doctype,row.name,'item_code',item.name);
    await frappe.model.set_value(row.doctype,row.name,'item_name_snapshot',item.item_name);
}
