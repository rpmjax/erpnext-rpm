# Baseline restore rehearsal — 2026-09-17

Baseline: 33aaca116838dc96c83e95fdaaa5d9fd7b7cc4e7, tag baseline/worklog-before-target-2026-09-17.
VM operator confirmed running image rpm-worklog-vm:33aaca116838, image ID sha256:237b3bd3a394219315db307e9877b1f3848c9ff9d0f703b36b4dfcd0ed803310.
Input: off-VM backup set 20260917_144522-worklog_internal. No secrets or backup contents are committed.

## Executed

- Isolated Docker project rpm-worklog-baseline-restore; new volumes, internal network, no published ports, no workers or scheduler service.
- Restored database and both file archives to baseline-restore.internal using the locally retained baseline image rpm-worklog-poc:baseline-20260917. This is the baseline source build, not a byte-identical copy of the VM image.
- Copied only backup encryption_key into isolated site configuration, retaining local DB credentials. Email muted and scheduler disabled.
- Ran baseline migration. SHA256 fingerprints of all rows (ordered by name) in Company, Department, User, Employee, Item, RPM Daily Work Log, RPM Work Log Line and RPM Work Log Review Event were identical before/after migration.
- Counts: Company 1; Department 14; User 35; Employee 32; Item 1; Work Log 1; Work Log Line 2; Review Event 0.
- Frappe System Settings timezone remains Asia/Taipei.
- Both attachment archives restored; there were zero regular attachment files, so this run does not prove restoration of nonempty attachments.
- RESTORE_PASS; verification process exit 0. Isolated services stopped afterward; volumes retained.

Initial verification harness failed due to its working-directory/site-path configuration after restore succeeded. Corrected the local harness and resumed read-only comparisons plus migration; did not reinitialize or overwrite the production site.

## Limits / next handoff

No production VM changes, no browser/login acceptance, no full production cutback exercise, and no new Work Target schema or functionality. The restored backup is a point-in-time copy; later production writes are not included. Backup verification is not evidence that new-schema rollback is safe.

Development branch: codex/work-target-phase1. master remains on the baseline. Next development requires its own isolated project/volumes; keep this restored baseline copy intact as a reference. Follow the approved design review, with final minimal requirements confirmed before feature implementation.

Local evidence (ignored, not versioned): .local/baseline-restore/restore.log, verify.log, restore.py and verify.py. Off-VM source backups remain in the user's erpnext-rpm-backups directory. These contain private data/settings and must not be pushed.
