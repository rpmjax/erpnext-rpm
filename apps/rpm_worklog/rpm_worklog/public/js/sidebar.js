// RPM custom DocTypes use module Custom; native app filtering can discard their sidebars.
(() => {
    const proto = frappe.ui.Sidebar.prototype;
    const original = proto.resolve_sidebar;
    proto.resolve_sidebar = function(entity, module) {
        if (!String(entity || '').startsWith('RPM ')) return original.call(this, entity, module);
        const candidates = this.get_workspace_sidebars(entity).filter(name =>
            frappe.boot.workspace_sidebar_item[name.toLowerCase()]);
        if (entity === 'RPM Work Target') {
            const entrances = [
                ['我的工作紀錄', 'RPM Work Log Pilot', 'RPM Daily Work Log'],
                ['直屬員工工作紀錄', 'RPM Work Log Manager Pilot', 'RPM Team Work Log Viewer'],
            ];
            const roles = frappe.boot.user?.roles || [];
            const eligible = entrances.filter(([name, role, link]) =>
                candidates.includes(name) && roles.includes(role) &&
                frappe.boot.workspace_sidebar_item[name.toLowerCase()].items.some(item =>
                    item.link_type === 'DocType' && item.link_to === link)
            ).map(([name]) => name);
            this.preferred_sidebars = eligible;
            // A fresh tab has no navigation context. Prefer the employee entrance;
            // preserve an existing manager context only when it is still eligible.
            return eligible.includes(this.sidebar_title) ? this.sidebar_title : eligible[0] || null;
        }
        // Legacy English sidebars may still be valid links, but omit new features.
        const primary = entity === 'RPM Daily Work Log' ? '我的工作紀錄'
            : entity === 'RPM Team Work Log Viewer' ? '直屬員工工作紀錄' : null;
        const modern = candidates.filter(name => ['我的工作紀錄', '直屬員工工作紀錄'].includes(name));
        if (modern.length) {
            this.preferred_sidebars = modern;
            if (modern.includes(primary)) return primary;
            return modern.includes(this.sidebar_title) ? this.sidebar_title : modern[0];
        }
        let resolved;
        try { resolved = original.call(this, entity, module); } catch (_) { /* stale browser preference */ }
        if (candidates.includes(resolved)) return resolved;
        this.preferred_sidebars = candidates;
        return candidates.includes(this.sidebar_title) ? this.sidebar_title : candidates[0] || null;
    };
})();
