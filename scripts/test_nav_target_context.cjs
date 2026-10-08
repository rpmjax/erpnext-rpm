const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2], 'utf8');
const own = '我的工作紀錄', team = '直屬員工工作紀錄';
function resolve(roles, current, ownLink = true, teamLink = true) {
    class Sidebar {
        get_workspace_sidebars() { return [team, own]; }
        resolve_sidebar() { throw new Error('Unexpected fallback'); }
    }
    const items = link => ({items: link ? [{link_type:'DocType',link_to:link}] : []});
    const frappe = {ui:{Sidebar},boot:{user:{roles},workspace_sidebar_item:{
        [own]:items(ownLink && 'RPM Daily Work Log'),
        [team]:items(teamLink && 'RPM Team Work Log Viewer'),
    }}};
    vm.runInNewContext(source, {frappe});
    const sidebar = new Sidebar(); sidebar.sidebar_title = current;
    return sidebar.resolve_sidebar('RPM Work Target','Custom');
}
const employee = 'RPM Work Log Pilot', manager = 'RPM Work Log Manager Pilot';
assert.equal(resolve([employee], team), own);
assert.equal(resolve([employee,manager]), own);
assert.equal(resolve([employee,manager], team), team);
assert.equal(resolve([manager]), team);
assert.equal(resolve([employee,manager], team, true, false), own);
assert.equal(resolve([], team), null);
assert.equal(resolve([employee], own, false), null);
console.log('NAV_CONTEXT_PASS: fresh tab, retained context, stale context, roles and valid entry');
