# Persian calendar architecture and validation

The standard Settings DocType owns `enable_persian_calendar` (default 0). The existing install/migrate default initializer handles fresh and upgraded sites without rewriting explicit values. `extend_bootinfo` reads the setting once per Desk load, including cached boots. Frappe caches `boot_session` output per user, so that hook alone would leave the toggle stale after reload. Static local assets load through app hooks. There are no per-field requests or backend date overrides.

When enabled, an isolated `ControlDate` subclass replaces the Desk constructor. Frappe v16's `ControlData` handles input creation and model writes. `format_for_input` renders Gregorian values as Jalali, `parse` converts input to Gregorian, and picker selections call the original model-facing `set_value` with Gregorian values. Frappe's ordinary validation, change events and document save pipeline remain in use. The constructor substitution is necessary because v16 has no app hook for choosing a Date control implementation. `iran_persian_calendar.uninstall()` restores the constructor; reload Desk to recreate existing controls. When disabled at boot, the original Date/Datetime classes are never replaced.

`Datetime` inherits the original Date class and has separate timezone, timepicker and state synchronization methods. It is deliberately untouched. Only Date control display areas are converted; global formatters, API serialization, exports and result cells are unchanged. Standard filters and dialogs inherit coverage through the Date constructor. DateRange/Between filters keep the native Gregorian range picker. Nonstandard third-party widgets are outside this scope.

The picker is a shared popup with Frappe theme variables, Persian month names, Saturday-first weeks, month navigation, today and clear buttons. It closes on outside click, focus leaving the popup, scroll, Escape and Tab from the input. Native buttons support Tab/Shift+Tab and Enter; ArrowDown transfers focus into the picker. `min_date`, `max_date`, picker `minDate`/`maxDate` options and `disabled_dates` are enforced on manual entry and selection. Other arbitrary Air Datepicker options are not implemented by the local picker.

Conversion is strict and deterministic. Python reuses the existing `jdatetime` dependency; official invoice imports the consolidated helper. The original JS implementation counts days from a fixed Gregorian epoch with the same 33-year leap residues. It uses UTC to avoid timezone/DST shifts for Date fields. The supported Jalali range is 1–9377; dates must map to Gregorian years at most 9999. Invalid entries preserve the prior model value and mark the field invalid rather than writing a malformed year to the backend. Empty values stay empty.

## Reference and licensing

Reviewed [persian_calendar_ERPNext](https://github.com/sfarbod/persian_calendar_ERPNext), including `license.txt` (MIT), `public/js/jalali_support/jalaali.js`, `public/js/jalali_support/persian_calendar.js` (Date/Datetime integration) and `jalali_support/utils/date_utils.py`. Its subclass integration informed the architecture. Its locale-dependent conversion, settings fetch/patch machinery and backend normalization were not ported. **No code was copied or adapted from that project**, so no additional MIT notice is required. All new picker/adapter/conversion code is original app code under this repository's license. `jdatetime` remains an existing installed dependency under its own license; its source was not vendored or copied.

## Automated checks

From the bench root:

```sh
env/bin/python apps/iran_localization/scripts/run_tests.py --site erp.localhost
node --test apps/iran_localization/iran_localization/tests/test_persian_calendar.mjs
bench --site erp.localhost migrate
bench build --app iran_localization
bench --site erp.localhost clear-cache
bench --site erp.localhost clear-website-cache
```

The Python runner rolls tests back. Prefer a working disposable test site if available. JS tests load the installed Frappe v16 control methods and exercise enabled/disabled behavior, programmatic values, parsing, clearing, bounds, invalid dates and round trips. The Python suite covers print conversion, leap/month/year boundaries, digits, empties, boot settings and unchanged database dates.

## Manual validation on erp.localhost

1. In Iran Localization Settings, enable **فعال‌سازی تقویم شمسی**, then save. Wait for Desk to reload.
2. Open a draft Sales Order, Sales Invoice or Purchase Invoice whose Date value is `2026-10-13`. Verify its input shows `1405/07/21` and readonly Date controls also display Jalali.
3. Focus the Date input. Check Persian month names and Saturday-first weekdays. Navigate to the previous/next month. Select `1405/07/22`; verify `1405/07/22` is displayed.
4. In the browser console inspect `cur_frm.doc[fieldname]` (for example `cur_frm.doc.transaction_date` on Sales Order). Verify `2026-10-14`, then save the draft and reload it. Verify the UI still shows `1405/07/22` and the saved document/API response still contains `2026-10-14`.
5. Enter `۱۴۰۵/۰۷/۲۱` and `١٤٠٥/٠٧/٢١`, leaving the input each time. Verify Gregorian `2026-10-13` in the model. Enter `1404/12/30`; verify an error and no change to the prior model date.
6. Clear the date on an optional field, then use Today. Check a new draft, an editable child-table Date field and a dialog Date field. Check query report and list filter Date controls return Gregorian filter values.
7. Check a leap Esfand (`1403/12/30`) and the following Farvardin (`1404/01/01`). Check input ArrowDown, button Tab/Enter and Escape, outside click, scrolling, narrow screens and dark theme. Observe browser console for errors.
8. Disable the checkbox and save. Reload other open Desk sessions. Verify the standard Gregorian picker returns and the saved document date remains `2026-10-14` (or the final Gregorian value you selected). Check a Datetime field remains standard in both modes.

Use draft documents and restore any test edits. No setting change itself writes document dates.

## Validation record (2026-10-13)

On Frappe 16.51.1 / ERPNext 16.50.0, all 52 Python tests passed (40 existing + 12 new) and all 11 Node tests passed. The cross-language test compares both conversion directions at year boundaries and leap Esfand dates across every supported Jalali year. Migration, app build and cache clearing succeeded on `erp.localhost`; `git diff --check` passed and both core repositories remained clean.

Headless Chromium against the live `erp.localhost` Desk verified Sales Order Date display/picker selection, Persian manual entry, ToDo save/reload/API Gregorian storage, clear/today, Escape, dialog Date controls, unchanged Datetime controls, the actual Date filter popover, month navigation, canonical Gregorian filter values and native Date picker restoration after disabling. No browser page errors or calendar asset failures occurred. The direct development server logged unrelated Socket.IO connection errors; a temporary proxy removed the 404 but exposed a realtime origin configuration error. Realtime deployment configuration was left unchanged. The temporary ToDo was deleted and the original calendar setting restored. A dark-theme screenshot was inspected. The browser save/reload check used ToDo rather than a real accounting document; repeat the manual draft transaction steps above for acceptance. Fresh-site installation was not separately exercised; the schema and existing default initialization use normal Frappe install/migrate behavior. The configured `test-iran.localhost` could not authenticate to its database, so the rollback-based Python suite ran on `erp.localhost`.
