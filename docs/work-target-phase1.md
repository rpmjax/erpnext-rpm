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

## Inline target selection (2026-09-18)
User confirmed that linked work entries appear on the target with review status.
This confirmation covers linked-row visibility and state, not every previous acceptance case.

Following a missed second-row link, show optional 跨日目標 immediately after 工作內容／物料
in the default work-entry grid. Every row remains independent; no automatic copying/linking.
Keep quantity, result and hours visible with explicit column widths. Detail/pencil remains available.
Existing user-customized grid layouts are preserved; users can add 跨日目標 via the grid gear.
No new quantity calculation, completion rule or production deployment.

Checks: migrated metadata order/editability/optional flag PASS; existing target permission/lifecycle
regression PASS; JS syntax PASS; external localhost:8086 login PASS.
Manual acceptance: reload a draft/new log; select a target directly on row 1, ensure row 2 stays blank;
select the same target on row 2, save, then refresh target summary and confirm both entries.
If a custom grid layout hides the new field, use its gear to select 跨日目標.

## Optional entry times (2026-09-18)
User accepted inline target selection. Continued the previously discussed optional same-day time range.
- Start/end default empty, optional, in row pencil detail immediately before Hours.
- A complete valid interval overwrites Hours with duration at the existing hours precision.
  Browser previews it; server computes again on save/validation, including forged manual-hour inputs.
- Either endpoint absent: preserve existing hours and allow manual entry; hours remain required/positive.
- Reject equal/reversed times, invalid clock values, and intervals that round to zero.
- No timer, automatic current-time default, break deduction, cross-midnight calculation, or nested segments.
- Existing records are not backfilled. Reviewed document edit locks remain unchanged.

Checks: isolated migration PASS; persisted calculation/manual fallback/midnight/invalid ranges/
document cap/review-lock tests PASS; target aggregation/review/security regression PASS;
JS syntax PASS; external 8086 login/form access PASS; optional/no-default metadata verified.
Browser acceptance pending. Production VM/master/baseline unchanged.

Manual acceptance (draft or new log, row pencil detail):
1. Without times, manually enter 1.25 hours and save; it remains 1.25.
2. Start 09:00, end 10:30: hours becomes 1.5; saved total reflects it.
3. Change end to 11:00: hours becomes 2.
4. Clear one time: retain 2; manually change to 0.75 and save successfully.
5. Equal times or end earlier than start must prevent saving.
6. Rows with time-derived hours linked to a target contribute to the same target hour totals.
No production SSH update for this experimental branch yet.

## Work log → target navigation (2026-09-18)
User accepted optional start/end time behavior. Added 前往關聯目標 above the entry grid.
- Distinct linked targets shown once each, with title and ID, refreshed on link changes/removal.
- Native permission-filtered get_list supplies target labels; unauthorized targets are not linked.
- Open target in a new tab to retain unsaved work; summary still counts saved rows only.
- No target, empty authorized result, failed lookup and stale responses handled explicitly.
- Existing employee target → own work-log navigation remains; manager form access is unchanged.
Checks: image/migration PASS, JS syntax PASS, external authenticated lookup returns own targets
and excludes them for the other employee. Manual browser acceptance pending.
Acceptance: reload a draft log, link two rows to one target (one shortcut), link another target
(two shortcuts), clear/remove rows (shortcuts update), click shortcut (new tab, edits retained).
Production VM/master remain unchanged; no SSH update needed for this development increment.

## Manager read-only log detail (2026-09-18)
User accepted work-log → target shortcuts. Manager target-summary rows now open a read-only dialog
with the full parent log, its current review state, return reason, times and work entries.
Rows linked to the current target are labelled 本目標; other rows are clearly distinguished.
The full log total is explicitly separate from target-linked hours. No save/review controls added.
Employee links to their own editable forms remain unchanged.
API rechecks target permission, common live scope, owner/employee consistency, cancellation and
actual target linkage on every request; it returns only selected display fields, without mutations.
Checks: target-summary regression including full-detail access/denial PASS; JS syntax PASS;
isolated migration PASS; authenticated external manager summary → detail API PASS.
Acceptance: manager login, open a direct employee target, click Work Log title (唯讀), verify
all parent rows and 本目標 labels, close dialog to return. No edit or review buttons should appear.
This increment awaits manual acceptance. Production VM/master unchanged.

## Team viewer visual hierarchy (2026-09-18)
User requested improved legibility of the long pipe-delimited summaries.
Replaced each summary with a responsive native details card: employee identity, textual/color review
badge, title, date/department/document ID, distinct hours and row count, explicit expand/collapse cue.
Expanded table keeps horizontal overflow within its container; numeric cells align right.
Review/history actions and backend authorization are unchanged. CSS scoped to the cards,
text escaped, native keyboard details behavior/focus retained. Empty/truncated results explicit.
Verification: JS syntax and installed Client Script checks PASS; isolated image/migration PASS.
Manual visual acceptance pending: reload team viewer, query dates, inspect collapsed and expanded
cards, narrow viewport, and ensure pending rows retain approve/return/history controls.

## Acceptance update and next-stage gate
User confirmed the manager read-only detail and requested continued development after the card-style update.
The linked-target, optional-time and navigation increments are manually accepted as recorded above.
No claim is made that production VM/master has been updated.

Before quantity progress code, confirm whether the first scope is personal/single-process/single-unit,
shared multi-process production, or release preparation of the current version.
Existing quantity fields have no enforced measurement unit or process. Do not retroactively treat
existing linked quantities as comparable or re-enable the previously disabled unit feature implicitly.

## Release preparation decision (2026-09-18)
User selected deferring quantity progress and preparing the current version for VM update.
The earlier notes about master being unchanged describe development at that time; release instructions
and migration evidence now live in vm-update-work-target-2026-09-18.md.
The VM itself is still operated by the user. Development test passwords/data are never shipped.

## Unreferenced target deletion (2026-09-21)
User approved the staged plan: deletion first for acceptance, then notifications/live refresh.
Only an enabled, active owning employee with the work-log employee role may delete an unreferenced
target. Other employees/managers cannot delete. Any current work-line reference, including a
cancelled parent, blocks deletion; archive instead. No user document was deleted by deployment.
Target deletion and entry-link validation lock the target to serialize concurrent writes.
Rollback regression PASS: owner unused deletion; other employee/manager denial; linked and cancelled
reference denial; existing target lifecycle/read-scope cases retained. No concurrent load test claimed.
Acceptance on 8086: create a disposable unused target as employee; page menu → Delete should succeed;
attempt on a linked target should fail with archive guidance. Refresh after migration for new permissions.
This patch remains on codex/work-target-phase1 pending acceptance; master/VM not updated.
