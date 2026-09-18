# Quantity progress — proposed first scope (pending user selection)

Current quantities are non-negative numbers without an enforced unit/process. They cannot yet be
summed into reliable progress merely because rows reference the same target.

Proposed personal first version:
- Explicit opt-in on a new target, positive planned quantity, declared unit and one completion definition.
- Work-entry quantity means newly completed units in that row; never cumulative-to-date.
- Approved quantities drive progress. Draft, pending and returned quantities remain separately visible.
- Work-entry result (In Progress/Completed/Blocked) does not itself prove target completion.
- No automatic closing; allow exceeding 100% to be visible instead of silently capping actual quantities.
- Do not retroactively count older rows whose measurement meaning was not declared.
- Lock measurement identity once referenced; decide handling of planned-quantity changes before coding.
- Rework and multiple production stages cannot be summed as new output. Shared production requires
  a separate participating-employee/process design and is outside this proposed first scope.

Acceptance examples once scope is agreed:
- 100 planned, 20 approved + 35 pending => 20% approved, 35 pending (not 55% approved).
- Approval of the 35 row => 55%; return/re-submit moves quantities between buckets without duplication.
- Unlinked/different-target/unauthorized/cancelled rows excluded; totals complete across pagination.
- Existing targets and manual-hour-only work continue unchanged.

This file records a proposal, not an implemented or approved quantity contract.

## User scope decision
Quantity progress is explicitly deferred. Prepare the accepted version for an existing VM update first.
This proposal is retained for future discussion only; no quantity-progress code is included in the release.
