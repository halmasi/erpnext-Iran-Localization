# Local verification — 2026-10-06

Version: `0.1.0`, unpublished. Tested on Frappe `15.121.3`, ERPNext `15.121.6`, Python `3.14`.

Completed checks:

- Read the original context, inspected Git HEAD `945f13e` and the existing uncommitted modular changes before editing.
- Migrated the existing test site successfully, including repeated migration runs.
- Preserved the original site pricing selections, zero overhead/markup and explicitly disabled core validation.
- Passed 38 module/database tests using `scripts/run_tests.py`.
- Verified saved settings and encrypted Password survive forced schema re-import.
- Verified safe defaults for an empty settings store and repeat setup calls.
- Verified direct, multilevel, batch-quantity and diamond BOM propagation with real submitted BOMs.
- Verified disabled pricing, cycle rejection, existing/new prices and protection of special customer prices.
- Verified real draft Sales Order creation, server prices, permissions and repeated-order request handling.
- Rendered the Persian template, generated a one-page PDF and parsed it successfully.
- Submitted a test Sales Invoice, verified the disabled taxpayer module does not block it,
  queued it once, dispatched through the simulated provider and rejected queuing after cancellation.
- Tested provider HTTP contracts using mocked network calls, changed-account protection,
  immutable payloads, explicit provider refresh and unknown-delivery handling.
- Passed Ruff checks, formatter checks, JavaScript syntax checks and `git diff --check`.
- Completed `bench build --app iran_localization`.
- Built local wheel and sdist; checked schemas/assets, docs/runner inclusion and context-file exclusion.
- Confirmed Frappe and ERPNext Git working trees remained clean.

Artifacts:

- `dist/iran_localization-0.1.0-py3-none-any.whl`
- `dist/iran_localization-0.1.0.tar.gz`
- Sample invoice PDF in the shared workspace: `/workspace/development/iran_invoice_sample.pdf`

Not verified in this session:

- A completely new Bench/site installation (empty settings initialization and existing-site migration were tested).
- Actual Dev Container restart or interactive browser layout (PDF generation and template rendering were tested).
- Real SMS delivery or real tax gateway submission with customer credentials.
- Government-specific tax wire schema, signing/encryption and final acceptance polling; these belong to the selected gateway/adapter.
- Public release: explicitly deferred by the user.

The existing site keeps new modules disabled until configured. Mock provider keys are initialized,
but no real external message was sent. The original `CODEX_CONTEXT.md` remains an unchanged historical snapshot.
