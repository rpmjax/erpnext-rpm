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
{
 const proto={resolve_sidebar(){return 'My Work Logs';}};
 const context={frappe:{ui:{Sidebar:{prototype:proto}},boot:{workspace_sidebar_item:{'my work logs':{},'我的工作紀錄':{},'直屬員工工作紀錄':{}}}}};
 vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),context);
 const sidebar=Object.create(proto);
 sidebar.sidebar_title='My Work Logs';
 sidebar.get_workspace_sidebars=()=>['My Work Logs','我的工作紀錄'];
 assert.equal(sidebar.resolve_sidebar('RPM Daily Work Log','Custom'),'我的工作紀錄');
 assert.equal(sidebar.resolve_sidebar('RPM Work Target','Custom'),'我的工作紀錄');
 sidebar.get_workspace_sidebars=()=>['直屬員工工作紀錄'];
 assert.equal(sidebar.resolve_sidebar('RPM Team Work Log Viewer','Custom'),'直屬員工工作紀錄');
 assert.equal(sidebar.resolve_sidebar('Customer','Selling'),'My Work Logs');
}
console.log('SIDEBAR_LEGACY_COEXISTENCE_PASS');
