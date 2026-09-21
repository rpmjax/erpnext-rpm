const fs = require('fs'), vm = require('vm'), assert = require('assert');
for (const result of [null, 'removed-sidebar', '我的工作紀錄', 'throw']) {
 const proto={resolve_sidebar(){if(result==='throw')throw Error('bad cache');return result;}};
 const context={frappe:{ui:{Sidebar:{prototype:proto}},boot:{workspace_sidebar_item:{'我的工作紀錄':{}}}}};
 vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),context);
 const sidebar=Object.create(proto);sidebar.get_workspace_sidebars=()=>['我的工作紀錄'];
 assert.equal(sidebar.resolve_sidebar('RPM Daily Work Log','Custom'),'我的工作紀錄');
 sidebar.get_workspace_sidebars=()=>[];
 assert.equal(sidebar.resolve_sidebar('RPM Daily Work Log','Custom'),null);
}
console.log('SIDEBAR_FALLBACK_PASS: filtered, stale, valid, corrupt preference; no unauthorized fallback');
