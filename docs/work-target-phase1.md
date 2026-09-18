# Work Target phase 1 — isolated development

Branch: codex/work-target-phase1. Production baseline: 33aaca1.

## Accepted foundation (2026-09-18)
- User manually accepted existing-page identity and access changes.
- Display surname + given name | employee_number; underlying Employee IDs unchanged.
- Common live Self/Team read predicates for reports and summaries; no administrator bypass.
- Report regression and authenticated HTTP employee/manager probes passed.

## Environment
- Local acceptance: http://127.0.0.1:8086, project rpm-work-target-phase1.
- Restored local PoC data, NOT production VM data. Use separately provided local test credentials.
- Internal database/backend network; frontend additionally uses ingress network for localhost publication.
- Previous install-test frontend occupied 8086 and was stopped; verify docker port AND external login.
- No workers/scheduler; production VM, master, and baseline restore volumes unchanged.
- Do not pull this experimental branch onto the production VM.

## Next increment
Lightweight optional self-owned Work Target, optional entry link, live direct-manager read only.
No quantity/progress calculation until UOM semantics are agreed. No start/end times in this increment.
