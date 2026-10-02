frappe.ui.form.on('RPM Worklog Settings', {
    async refresh(frm) {
        frm.disable_save();
        frm.doc.__unsaved = 0;
        const w = frm.fields_dict.controls.$wrapper.empty();
        let current = null, selected = '', busy = false, version = 0;
        const status = $('<p role="status">').appendTo(w);
        const picker = $('<div class="form-group">').appendTo(w);
        $('<label>').text('營運公司').appendTo(picker);
        const input = $('<input type="search" class="form-control" placeholder="輸入公司名稱搜尋" aria-label="搜尋營運公司">').appendTo(picker);
        const choices = $('<select class="form-control" aria-label="選擇營運公司">').appendTo(picker);
        $('<p>').text('公司設定決定 Management 的分析範圍；不會自動授予角色或修改 Employee 公司。').appendTo(w);
        const save = $('<button class="btn btn-primary" type="button" disabled>儲存營運公司</button>').appendTo(w);
        const display = () => {
            status.text(current ? '目前營運公司：' + current : '尚未設定營運公司；公司分析暫不可用。');
            choices.empty().append($('<option>').val('').text('請搜尋並選取公司'));
            if (current) choices.append($('<option>').val(current).text(current));
            choices.val(current || ''); selected = current || '';
            save.prop('disabled',true);
        };
        try {
            const {message:d} = await frappe.call('rpm_worklog.settings.read');
            if (!w[0].isConnected) return;
            current=d.company; display();
        } catch (e) {
            status.text('無法讀取設定；僅限系統管理者。'); picker.hide(); return;
        }
        const search = async () => {
            const ticket=++version;
            try {
                const {message:d} = await frappe.call('rpm_worklog.settings.search_companies',{text:input.val()});
                if (ticket!==version || !w[0].isConnected) return;
                choices.empty().append($('<option>').val('').text('請選取公司'));
                d.items.forEach(c=>choices.append($('<option>').val(c.value).text(c.label)));
                selected=''; save.prop('disabled',true);
                status.text(d.has_more ? '候選超過 20 筆，請輸入更完整的名稱。' : '請選擇公司；目前設定：' + (current || '未設定'));
            } catch (e) { if(ticket===version) status.text('搜尋失敗，請重試。'); }
        };
        let timer;
        input.on('input',()=>{++version; clearTimeout(timer);timer=setTimeout(search,250);});
        input.on('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);search();}});
        choices.on('change',()=>{selected=choices.val();save.prop('disabled',busy || !selected || selected===current);});
        save.on('click',()=>{
            if(busy || !selected || selected===current)return;
            const next=selected, previous=current;
            frappe.confirm('變更營運公司會改變公司分析的授權資料範圍，確定儲存？',async()=>{
                if(busy)return;
                busy=true;save.prop('disabled',true);picker.find('input,select').prop('disabled',true);
                ++version;clearTimeout(timer);
                try {
                    const {message:d}=await frappe.call({method:'rpm_worklog.settings.save',type:'POST',
                        args:{company:next,expected_company:previous || ''}});
                    current=d.company;display();
                    frappe.show_alert({message:'營運公司已儲存，請重新開啟分析查詢。',indicator:'green'});
                } catch(e) {
                    status.text('儲存未確認成功，請重新載入設定後核對。');
                } finally { busy=false;picker.find('input,select').prop('disabled',false); }
            });
        });
    }
});
