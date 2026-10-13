const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const ctx = {frappe:{ui:{form:{on(){}}}}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'),ctx);
const range = (p,d) => Array.from(ctx.rpm_distribution_range(p,d) || []);
assert.deepEqual(range('週','2026-10-11'),['2026-10-05','2026-10-11']);
assert.deepEqual(range('週','2026-01-01'),['2025-12-29','2026-01-04']);
assert.deepEqual(range('月','2024-02-12'),['2024-02-01','2024-02-29']);
assert.deepEqual(range('日','2026-10-12'),['2026-10-12','2026-10-12']);
assert.deepEqual(range('自訂','2026-10-12'),[]);
console.log('DISTRIBUTION_PRESETS_PASS');
const nodes=[];
class Element {
    constructor(tag) {this.tag=tag; this.attrs={}; this.content=''; this.children=[]; nodes.push(this);}
    attr(k,v) {this.attrs[k]=v;return this;}
    css() {return this;}
    text(v) {this.content=v;return this;}
    html(v) {this.content=v;return this;}
    append(...v) {this.children.push(...v);return this;}
    appendTo(parent) {parent.append(this);return this;}
    find() {return {each(){}};}
}
ctx.$=tag=>new Element(tag);
ctx.__=x=>x;
ctx.frappe.utils={escape_html:x=>x.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')};
const data={employee:{label:'<employee>'},scope:'Self',from_date:'2026-10-01',to_date:'2026-10-01',review_state:'All',
    totals:{reported_hours:8.4,line_count:2,activity_type_count:1,unclassified_line_count:0},
    groups:[{activity_type:'<type>',display_label:'<type>',hours:8.4,percentage:100,line_count:2,
        top_items:[{work_item:'<script>alert(1)</script>',hours:8.4,line_count:2}],
        remaining:{distinct_item_count:0,line_count:0,hours:0}}]};
ctx.rpm_render_distribution(new Element('output'),data);
const svg=nodes.find(n=>n.content.includes?.('<svg'));
assert(svg && svg.content.includes('<circle'));
assert(!svg.content.includes('<script>'));
assert(svg.content.includes('&lt;script&gt;'));
assert(nodes.some(n=>n.attrs.title?.includes('8.400 小時｜100.00%｜2 筆')));
assert(nodes.some(n=>n.tag==='<summary>'));
nodes.length=0;
ctx.rpm_render_distribution(new Element('output'), {...data,groups:[]});
assert(nodes.some(n=>n.content==='無符合紀錄'));
assert(!nodes.some(n=>n.content.includes?.('<svg')));
console.log('DISTRIBUTION_RENDER_PASS: tooltip, accessible details, escaped SVG, empty state');
assert.equal(ctx.rpm_candidate_index(-1,'ArrowDown',3),0);
assert.equal(ctx.rpm_candidate_index(-1,'ArrowUp',3),2);
assert.equal(ctx.rpm_candidate_index(2,'ArrowDown',3),0);
assert.equal(ctx.rpm_candidate_index(0,'ArrowUp',3),2);
assert.equal(ctx.rpm_candidate_index(-1,'ArrowDown',0),-1);
assert(svg.content.includes('role="button"') && svg.content.includes('aria-controls='));
console.log('DISTRIBUTION_INTERACTION_PASS: candidate navigation, chart button semantics');
