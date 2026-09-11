frappe.ui.form.on('RPM Work Log Line', {
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
                    .text(`${item.name} | ${item.item_name} | ${item.stock_uom}`).appendTo(area).on('click', async () => {
                        await frappe.model.set_value(cdt,cdn,'item_code',item.name);
                        await frappe.model.set_value(cdt,cdn,'item_name_snapshot',item.item_name);
                        if (!(row.work_item || '').trim()) await frappe.model.set_value(cdt,cdn,'work_item',item.item_name);
                        if (!row.uom) await frappe.model.set_value(cdt,cdn,'uom',item.stock_uom);
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
