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

## Target linked-work summary (2026-09-18)

Implemented in the target form under 關聯工作與工時:
- Read-only, saved data across all dates; refresh button does not save the target.
- Total hours, approved hours, not-yet-approved hours; Draft/Pending Review/Returned/Approved breakdown.
- Entry-level detail: date, work log/row, activity, work content, result, hours, review state.
- Only matching child rows are summed, never the parent total_hours. Cancelled parents excluded.
- Fifty rows per page; aggregate totals cover all matches. Archived targets retain their history.
- Target permission plus common live Self/Team predicates; target owner/employee must match the source log.
- Employee may open own log from detail; managers read the detail here without an inaccessible form link.
- No completion percentage, quantity sums or automatic target closing.

### Verification
Target summary rollback tests PASS: mixed linked/unlinked rows, actual submit/return/approve
rebucketing, 58 rows across two pages with unchanged full totals, cancelled/cross-owner
fixtures excluded, archive retained, invalid pagination and removed-manager/disabled-user/Guest denied.
Existing target regression PASS. JS syntax PASS. Migration and metadata checks PASS.
External 8086 HTTP login/list/summary PASS for employee and manager with existing targets; Guest denied.
Manual acceptance of this summary increment remains pending.

### Acceptance with predictable totals
Use employee j250301@outlook.com and a NEW target named 驗收－跨日工時 (to isolate existing data).
1. Create a draft work log with target-linked rows 1.25h and 0.75h, plus an unrelated row 7h.
2. Create another date's work log with one target-linked row 3h. Save both logs.
3. Open target, scroll to 關聯工作與工時: 2 logs, 3 linked rows, total 5h, Draft 5h, Approved 0h.
   The unrelated 7h must not be included.
4. Submit the second log (whole document). Refresh target summary: Draft 2h, Pending Review 3h, total 5h.
5. As manager t870602rpm@outlook.com, approve that log in the team viewer. Refresh target:
   Approved 3h, not-yet-approved 2h, total 5h. Manager sees summary but cannot edit the target.
6. Optionally test return before approval: 3h moves from Pending Review to Returned, total remains 5h.
7. A newly created target without linked saved rows shows an empty explanation and zero totals.
8. Target status remains manually controlled; hours do not imply completion.

Refresh the browser after deployment to load the new Client Script. Use local acceptance credentials;
production credentials are not synchronized. Production VM update remains deferred on this branch.
