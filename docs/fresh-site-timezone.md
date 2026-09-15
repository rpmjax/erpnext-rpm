# Fresh-site timezone policy and root cause (2026-09-15)

## Scope

Only newly created sites from deploy/init_site.py receive `rpm_worklog_fresh_timezone=Asia/Taipei`. Their Frappe System Settings time_zone and default are initialized to Asia/Taipei. No OS/container TZ change is used as a substitute for the Frappe setting.

The initializer rejects an existing site directory before changing settings. build/update/repair-workers do not set the marker or call timezone.initialize. Existing sites, including the manually corrected VM, are not reset or recreated.

During a marked site's unfinished setup wizard, a scoped System Settings before_validate hook preserves Asia/Taipei; the setup_wizard_stages hook also normalizes the wizard args before the global-settings task, including the timezone passed to Frappe's standard-user background job. After setup_complete is true these hooks do nothing. An unmarked existing site is never subject to this policy, even if its wizard is unfinished.

## Root cause, verified against the deployed image

Versions: Bench 5.31.0, Frappe 16.33.0, ERPNext 16.34.1.

1. The old initializer ran new-site/install-app/migrate but never initialized Frappe time_zone. An untouched isolated deployment had an empty System Settings value and no time_zone default.
2. `frappe/geo/country_info.json` has a Taiwan entry with TWD and formatting settings, but no `timezones` key.
3. `frappe/desk/page/setup_wizard/setup_wizard.js`, bind_region_events, rebuilds the timezone Select on country change. It appends the country's timezones (empty for Taiwan), then all_timezones, and saves the Select's first selected value.
4. `frappe.utils.momentjs.get_all_timezones()` starts with Africa/Abidjan, Africa/Accra, Africa/Addis_Ababa. Thus Taiwan's empty list falls back to Africa/Abidjan.
5. `setup_wizard.py:update_system_settings` saves args.timezone directly to System Settings.time_zone; it does not infer Asia/Taipei from Taiwan.
6. `core/doctype/system_settings/system_settings.json` marks time_zone read_only=1, explaining the inability to correct it on that settings page.

The actual country-change handler was extracted from the running image and executed in Node with its real Taiwan/all_timezones data and a minimal Select stub. Starting at Asia/Taipei and changing country to Taiwan reproduced Africa/Abidjan. This reproduces the code path; the historical production browser request was not captured or inspected.

An additional prefill mismatch exists in that wizard version: it requests `timezone` from System Settings but reads `time_zone`. The fix does not depend on prefill or patch Frappe Core.

## Verification

Fresh deployment ends with the explicit check:

```
Frappe System Settings timezone -> Asia/Taipei -> PASS
```

This is executed through a separate bench process so it reads the persisted setting. It must pass before RPM_INIT_SUCCESS. It is not added as a hard-coded assertion to normal existing-site update/verify commands: other existing timezone choices are valid and must be preserved.

`scripts/test_fresh_timezone.py` is restricted to the disposable timezone.internal test. It checks fresh initialization, actual Frappe stage construction, incorrect wizard input protection, completed-site changes, unmarked-site preservation and rejection of initialize on a completed site. It intentionally saves Pacific/Auckland on the isolated test site to verify subsequent migration does not force Asia/Taipei.

The user has already corrected the VM manually; no VM commands or production-data modifications are part of this fix. Pull/build/update at the next normal maintenance window; never rerun init on the existing VM.

Executed results: a second isolated project (rpm-worklog-timezone-test-v2) completed full fresh initialization from empty volumes, printed the timezone PASS twice and RPM_INIT_SUCCESS, and exited 0. The guard test passed on timezone.internal. A real bench migrate subsequently exited 0, and an independent console read asserted Pacific/Auckland remained unchanged (EXISTING_TIMEZONE_PRESERVED_AFTER_MIGRATE).
