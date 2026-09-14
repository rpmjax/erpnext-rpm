frappe.ui.form.on('RPM Daily Work Log', {
    refresh(frm) { rpm_material_toolbar(frm); }
});
function rpm_material_toolbar(frm) {
    const area = frm.fields_dict.work_entry_help.$wrapper;
    area.empty();
    $('<p>').text('可直接填寫工作內容；需要物料時，在這裡選擇工作列後操作，不必展開鉛筆明細。').appendTo(area);
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
    lines_add(frm) { rpm_material_toolbar(frm); },
    lines_remove(frm) { rpm_material_toolbar(frm); },
    item_code(frm) { rpm_material_toolbar(frm); },
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
                        await frappe.model.set_value(cdt,cdn,'item_code',item.name);
                        await frappe.model.set_value(cdt,cdn,'item_name_snapshot',item.item_name);
                        if (!(row.work_item || '').trim()) await frappe.model.set_value(cdt,cdn,'work_item',item.item_name);
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
