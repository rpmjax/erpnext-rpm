/* Shared analytical dataset; this dialog never edits source work logs. */
async function rpm_worklog_analysis_open() {
    const {message:options} = await frappe.call('rpm_worklog.analysis.options');
    const labels={Self:'本人',Team:'有效直屬員工',Organization:'公司全員（含離職歷史）'};
    const esc=x=>frappe.utils.escape_html(String(x ?? ''));
    const d=new frappe.ui.Dialog({title:'工作明細分析／匯出',size:'extra-large',fields:[
        {fieldname:'scope',label:'查詢範圍',fieldtype:'Select',options:options.scopes.map(value=>({value,label:labels[value]})),default:options.scopes.includes('Organization')?'Organization':options.scopes[0]},
        {fieldname:'from_date',label:'開始日期',fieldtype:'Date',default:frappe.datetime.month_start(),reqd:1},
        {fieldname:'to_date',label:'結束日期',fieldtype:'Date',default:frappe.datetime.get_today(),reqd:1},
        {fieldname:'review_state',label:'審核狀態',fieldtype:'Select',default:'All',options:[{value:'All',label:'全部'},{value:'Draft',label:'草稿'},{value:'Pending Review',label:'待審'},{value:'Returned',label:'退回修改'},{value:'Approved',label:'已核准'}]},
        {fieldname:'employee',fieldtype:'HTML'},
        {fieldname:'department',fieldtype:'HTML'},
        {fieldname:'results',fieldtype:'HTML'}
    ],primary_action_label:'查詢',primary_action:()=>run(0)});
    const w=d.fields_dict.results.$wrapper;
    let version=0, current=null;
    const fields=['scope','from_date','to_date','review_state'];
    const chosen={employee:new Map(),department:new Map()};
    const pickers=[];
    const values=()=>({...Object.fromEntries(fields.map(key=>[key,d.get_value(key)])),
        employee:[...chosen.employee.keys()],department:[...chosen.department.keys()]});
    const signature=()=>JSON.stringify(values());
    const invalidate=()=>{version++;current=null;w.empty().text('條件已變更，請按查詢。');};
    fields.forEach(key=>d.fields_dict[key].df.onchange=invalidate);
    let closed=false;
    for(const kind of ['employee','department']) {
        const title=kind==='employee'?'員工（工號／姓名搜尋，可多選）':'紀錄部門（名稱搜尋，可多選）';
        const box=d.fields_dict[kind].$wrapper;
        box.html(`<label>${title}</label><div class="selected-items"></div>
            <input type="search" class="form-control" aria-label="${title}" placeholder="輸入部分文字，選取下方候選">
            <button type="button" class="btn btn-default search">搜尋候選</button>
            <button type="button" class="btn btn-default clear">清除選取</button>
            <div class="candidate-items"></div><p class="text-muted hint" aria-live="polite"></p>`);
        const input=box.find('input'),list=box.find('.candidate-items'),hint=box.find('.hint');
        let serial=0,timer;
        const render=()=>{
            const area=box.find('.selected-items').empty();
            chosen[kind].forEach((label,value)=>$('<button type="button" class="btn btn-default btn-sm">')
                .text(label+' ×').attr('aria-label','移除 '+label).on('click',()=>{
                    chosen[kind].delete(value);render();invalidate();
                }).appendTo(area));
        };
        const search=async()=>{
            const ticket=++serial,scope=d.get_value('scope');
            if(!scope)return;
            list.empty();hint.text('搜尋中…');
            try {
                const {message:r}=await frappe.call('rpm_worklog.analysis.search_filters',{scope,kind,text:input.val()});
                if(closed||ticket!==serial||scope!==d.get_value('scope'))return;
                r.items.forEach(item=>$('<button type="button" class="btn btn-default btn-sm">').text(item.label)
                    .on('click',()=>{
                        if(chosen[kind].size>=100&&!chosen[kind].has(item.value)){frappe.msgprint('每欄最多選取 100 項');return;}
                        chosen[kind].set(item.value,item.label);render();invalidate();
                    }).appendTo(list));
                hint.text(r.has_more?'超過 20 個候選，請輸入更完整的文字。':r.items.length?'點選可加入多個條件。':'沒有符合的候選。');
            } catch(e){if(ticket===serial)hint.text('搜尋失敗，請重試。');}
        };
        input.on('input',()=>{++serial;clearTimeout(timer);timer=setTimeout(search,250);});
        input.on('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);search();}});
        box.find('.search').on('click',search);
        box.find('.clear').on('click',()=>{chosen[kind].clear();render();invalidate();});
        const reset=()=>{++serial;clearTimeout(timer);chosen[kind].clear();input.val('');list.empty();render();
            hint.text('未選取＝不額外限制。候選來自可讀工作紀錄，不受日期限制。');};
        pickers.push(reset);reset();
    }
    d.fields_dict.scope.df.onchange=()=>{pickers.forEach(reset=>reset());invalidate();};
    d.onhide=()=>{closed=true;version++;current=null;pickers.forEach(reset=>reset());};
    async function run(offset) {
        const selected=values();
        if(!selected.from_date||!selected.to_date) {frappe.msgprint('請選擇日期');return;}
        const {scope,...filters}=selected;
        const key=signature(), request=++version;
        current=null;w.text('查詢中…');
        try {
            const {message:data}=await frappe.call('rpm_worklog.analysis.query',{scope,filters,offset,page_size:50});
            if(request!==version||key!==signature())return;
            current={scope,filters,key};
            w.html(`<p><strong>${esc(labels[scope])}${scope==='Organization'?' · '+esc(options.company):''}</strong><br>
                共 ${data.total_logs} 張紀錄／${data.total_rows} 筆工作列／申報工時 ${esc(Number(data.reported_hours).toFixed(3))} 小時。</p>
                <p class="text-muted">部門採工作紀錄保存值；主管／公司採目前員工資料。此處工時不是出勤或加班認定。</p>
                <div class="analysis-download"><button class="btn btn-default" data-format="CSV">下載完整 CSV</button>
                <button class="btn btn-default" data-format="XLSX">下載完整 XLSX</button></div>
                <p>${data.total_rows?`${offset+1}–${offset+data.rows.length}`:'0'} ／ ${data.total_rows} 筆；下載包含全部符合條件的工作列與 28 個欄位。</p>
                <div class="table-responsive"><table class="table table-bordered"><thead><tr>
                ${['日期','員工／工號','紀錄／列','內容／物料','數量','工時','審核狀態'].map(x=>`<th>${x}</th>`).join('')}
                </tr></thead><tbody>${data.rows.map((r,i)=>`<tr><td>${esc(r.work_date)}</td><td>${esc(r.employee_name)}<br>${esc(r.employee_number)}</td>
                <td><button class="btn btn-link" data-row="${i}">${esc(r.work_log)}／${esc(r.line_index)}</button></td>
                <td>${esc(r.work_item)}<br>${esc(r.item_code)}</td><td>${esc(r.quantity)}</td><td>${esc(r.hours)}</td><td>${esc(__(r.review_state))}</td></tr>`).join('')}</tbody></table></div>
                <button class="btn btn-default analysis-prev" ${offset===0?'disabled':''}>上一頁</button>
                <button class="btn btn-default analysis-next" ${data.has_more?'':'disabled'}>下一頁</button>`);
            w.find('[data-row]').on('click',function(){
                const row=data.rows[Number(this.dataset.row)];
                frappe.msgprint({title:'工作列唯讀明細',message:`<dl>${data.columns.map(c=>`<dt>${esc(c)}</dt><dd style="white-space:pre-wrap">${esc(row[c])||'—'}</dd>`).join('')}</dl>`});
            });
            w.find('.analysis-prev').on('click',()=>run(Math.max(0,offset-50)));
            w.find('.analysis-next').on('click',()=>run(offset+50));
            w.find('[data-format]').on('click',async function(){
                if(!current||current.key!==signature()){invalidate();return;}
                const button=$(this).prop('disabled',true);
                try {
                    const response=await fetch('/api/method/rpm_worklog.analysis_export.download',{
                        method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded','X-Frappe-CSRF-Token':frappe.csrf_token},
                        body:new URLSearchParams({scope:current.scope,filters:JSON.stringify(current.filters),file_type:this.dataset.format})});
                    if(!response.ok)throw new Error('download');
                    const url=URL.createObjectURL(await response.blob());
                    const a=document.createElement('a');a.href=url;a.download='worklog-analysis.'+this.dataset.format.toLowerCase();a.click();
                    setTimeout(()=>URL.revokeObjectURL(url),1000);
                } catch(e) {frappe.msgprint('匯出失敗。請確認權限、縮小日期範圍後重試；單次最多 50,000 筆工作列。');}
                finally {button.prop('disabled',false);}
            });
        } catch(e) {if(request===version){current=null;w.text('查詢失敗，請檢查權限與條件後重試。');}}
    }
    d.show();
    w.text('請確認範圍與日期，按「查詢」載入工作明細。');
}
