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

## Work Target initial increment (2026-09-18)
- RPM Work Target: title, optional manufacturing-order text, optional dates, notes, Open/Closed/Archived.
- Self-owned by the authenticated employee; ownership immutable. Current direct manager can read only.
- Target link is optional in Work Entry detail (pencil). Native Link supports selecting/creating a target.
- Picker offers own Open targets only. Server rejects cross-owner links even with forged requests.
- Existing closed/archived links remain; new links require Open. Archive instead of hard delete.
- Sidebars add 跨日工作目標. Existing sidebar links are preserved, including legacy translated links.
- No quantity/progress totals, timer fields, CEO role, or manufacturing transaction integration yet.

### Verification
Rollback target tests: create, optional/unlinked entries, cross-owner denial, manager read-only,
live Reports To removal, immutable ownership, date validation, archive retention. PASS.
Report aggregation/security regression PASS. JS syntax PASS. Fresh image migrate PASS.
External localhost:8086 login + target list API + form metadata probes passed for employee and manager.
Browser interaction remains for user acceptance. This increment has NOT been manually accepted yet.

### Manual acceptance
1. Login as local employee j250301@outlook.com using the local acceptance-accounts file.
2. Open /desk/rpm-work-target and create a target with a name; other descriptive fields optional.
3. Open a draft daily log, expand a work-entry pencil, select 跨日工作目標（選填） and save.
4. Save another entry with no target; ordinary work logging must still work.
5. Login as t870602rpm@outlook.com: see direct employee target; editing/creation unavailable.
6. Login as the other employee: cannot see the first employee target.
7. Owner sets target Archived: existing log link remains; new picker no longer offers it.

No SSH update to production for this experimental increment. Keep VM at master baseline.
