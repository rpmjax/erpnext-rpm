// RPM custom DocTypes use module Custom; native app filtering can discard their sidebars.
(() => {
    const proto = frappe.ui.Sidebar.prototype;
    const original = proto.resolve_sidebar;
    proto.resolve_sidebar = function(entity, module) {
        if (!String(entity || '').startsWith('RPM ')) return original.call(this, entity, module);
        const candidates = this.get_workspace_sidebars(entity).filter(name =>
            frappe.boot.workspace_sidebar_item[name.toLowerCase()]);
        let resolved;
        try { resolved = original.call(this, entity, module); } catch (_) { /* stale browser preference */ }
        if (candidates.includes(resolved)) return resolved;
        this.preferred_sidebars = candidates;
        return candidates.includes(this.sidebar_title) ? this.sidebar_title : candidates[0] || null;
    };
})();
