const fs = require('fs'), vm = require('vm'), assert = require('assert');
const handlers = {}, writes = [];
let approve = true, duringConfirm = () => {};
const context = {frappe:{ui:{form:{on:(name,h)=>handlers[name]=h}},utils:{escape_html:s=>s},
 confirm:(_,yes,no)=>{duringConfirm(); (approve?yes:no)();},model:{set_value:async(...args)=>writes.push(args)}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('apps/rpm_worklog/rpm_worklog/public/js/item_picker.js','utf8'),context);
(async()=>{
 const first={name:'first',doctype:'Line',idx:1,work_item:'manual content'};
 const second={name:'second',doctype:'Line',idx:2,work_item:''};
 const frm={doc:{lines:[first,second],review_state:'Draft'}};
 const item={name:'CF-FS0061',item_name:'Test'};
 await context.rpm_choose_item(frm,second,item);
 assert.equal(writes.length,3); assert(writes.every(w=>w[1]==='second')); assert.equal(first.work_item,'manual content');
 writes.length=0; approve=false; await context.rpm_choose_item(frm,first,item); assert.equal(writes.length,0);
 approve=true; duringConfirm=()=>{frm.doc.lines=[second];}; await context.rpm_choose_item(frm,first,item); assert.equal(writes.length,0);
 duringConfirm=()=>{}; frm.doc.lines=[first,second]; frm.doc.review_state='Approved';
 await context.rpm_choose_item(frm,second,item); assert.equal(writes.length,0);
 console.log('MATERIAL_TARGET_PASS: second row only, cancel, deleted target, locked record');
})().catch(e=>{console.error(e);process.exit(1)});
