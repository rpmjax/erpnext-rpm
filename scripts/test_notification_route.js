const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(process.argv[2], 'utf8');
for (const via of ['url', 'route_options']) {
    let handler, called;
    const element = {val(){return '2026-09-21';}, on(){}};
    const context = {
        URLSearchParams, window:{location:{search:via === 'url' ? '?work_log=RWL-test' : ''}},
        __:x=>x, frappe:{ui:{form:{on:(name,h)=>handler=h}},
            route_options:via === 'route_options' ? {work_log:'RWL-test'} : {}, datetime:{get_today:()=> '2026-09-21'}}
    };
    vm.createContext(context); vm.runInContext(source,context);
    context.load_team = (...args)=>called=args;
    handler.refresh({add_custom_button(){},disable_save(){},set_df_property(){},doc:{},
        page:{set_indicator(){},set_primary_action(){}},fields_dict:{results:{$wrapper:{html(){},find(){return element;}}}}});
    assert.equal(called[3],'RWL-test'); assert.equal(called[1],null);
}
console.log('NOTIFICATION_ROUTE_PASS: URL and Frappe route options open exact log without date input');
