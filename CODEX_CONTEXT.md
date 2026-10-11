# CODEX_CONTEXT.md

## Project
ERPNext / Frappe self-hosted business platform for a manufacturing company.

The long-term goal is a modular, reusable, installable Frappe app named:

`iran_localization`

The app should work as a standalone plugin for future ERPNext projects and may later be published publicly for free.

Do **not** modify ERPNext core unless absolutely necessary. Prefer:
- Frappe hooks
- fixtures
- custom DocTypes
- custom fields
- service modules
- patches / migrations
- install hooks

The app must remain modular and avoid project-specific hard-coding.

---

## Business requirements

The target business is a manufacturing company that currently has about 20 employees but may grow to ~500 employees.

Expected sales growth may be ~10x.

The platform should eventually cover:
- ERP
- Accounting
- Manufacturing
- Inventory
- Purchasing
- Sales
- HR / Payroll
- CRM
- Website / headless commerce API
- SMS notifications
- Helpdesk
- Localization for Iran
- Optional Iranian Taxpayer System integration
- Automatic product pricing based on raw-material prices

Self-hosting and avoiding per-user license costs are important.

---

# Current environment

## Host
- Arch Linux / Omarchy
- Docker
- Docker Compose
- VS Code Dev Containers

## Frappe stack
- Frappe: `15.121.3`
- ERPNext: `15.121.6`
- iran_localization: `0.0.1`
- Branch for Frappe / ERPNext: `version-15`
- iran_localization branch: `develop`

## Bench
Bench path inside Dev Container:

`/workspace/development/frappe-bench`

Site:

`erp.localhost`

For local development, `http://localhost:8000` is currently the stable URL.

Run the development stack with:

```bash
cd /workspace/development/frappe-bench
bench start
```

---

# Docker / Dev Container notes

The dev container uses:
- MariaDB 11.8
- redis-cache
- redis-queue

The Bench common config currently uses service hostnames:

```json
{
  "db_host": "mariadb",
  "db_type": "mariadb",
  "redis_cache": "redis://redis-cache:6379",
  "redis_queue": "redis://redis-queue:6379",
  "redis_socketio": "redis://redis-queue:6379"
}
```

Important: there was a Docker networking issue after restarting the host.

At one point two compose stacks existed at the same time:
- `devcontainer-*`
- `frappe_docker_devcontainer-*`

The extra `devcontainer-*` stack was removed.

The correct active stack is now the `frappe_docker_devcontainer-*` stack.

The Frappe container must be attached to the same network as:
- `redis-cache`
- `redis-queue`
- `mariadb`

If `bench start` fails with:

`getaddrinfo EAI_AGAIN redis-queue`

check Docker networking first.

Useful checks:

```bash
getent hosts redis-queue
getent hosts redis-cache
getent hosts mariadb
```

These should all resolve successfully.

---

# Installed apps

Current site apps:

```text
frappe            15.121.3
erpnext           15.121.6
iran_localization 0.0.1
```

---

# Language

ERPNext UI has been switched to Persian for team usability.

Iran localization beyond UI language is implemented in the custom app.

---

# iran_localization app

Path:

`/workspace/development/frappe-bench/apps/iran_localization`

Main design rule:

**Keep the app modular, reusable, and installable on other ERPNext sites.**

Current modular structure:

```text
iran_localization/
├── iran_localization/
│   ├── hooks.py
│   ├── fixtures/
│   │   ├── custom_field.json
│   │   └── doctype.json
│   └── modules/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── validation.py
│       └── pricing/
│           ├── __init__.py
│           └── service.py
```

Pricing logic was previously in:

`iran_localization/pricing.py`

and was moved to:

`iran_localization/modules/pricing/service.py`

Validation logic was previously in:

`iran_localization/validation.py`

and was moved to:

`iran_localization/modules/core/validation.py`

---

# Hooks

Current `doc_events` structure should be equivalent to:

```python
doc_events = {
    "Company": {
        "validate": "iran_localization.modules.core.validation.validate_iran_fields"
    },
    "Customer": {
        "validate": "iran_localization.modules.core.validation.validate_iran_fields"
    },
    "Supplier": {
        "validate": "iran_localization.modules.core.validation.validate_iran_fields"
    },
    "Item Price": {
        "on_update": "iran_localization.modules.pricing.service.update_product_prices_from_raw_material"
    },
}
```

Verify the current `hooks.py` before changing anything.

Useful runtime check:

```python
frappe.get_hooks("doc_events").get("Item Price")
```

Expected:

```python
{
    "on_update": [
        "iran_localization.modules.pricing.service.update_product_prices_from_raw_material"
    ]
}
```

---

# Fixtures

`hooks.py` includes fixtures for:

1. `Custom Field`
2. `Iran Localization Settings` DocType

Current fixture files:

```text
iran_localization/fixtures/custom_field.json
iran_localization/fixtures/doctype.json
```

The fixture export command is:

```bash
bench --site erp.localhost export-fixtures
```

Important lesson:

When new fields are added to `Iran Localization Settings`, the fixture must be re-exported **before running migrate**, otherwise an older `doctype.json` can overwrite the new DocType structure.

---

# Iranian company/customer/supplier fields

Custom fields exist for:

## Company
- `iran_localization_section`
- `iran_national_id`
- `iran_economic_code`
- `iran_registration_number`
- `iran_postal_code`

## Customer
- `iran_tax_section`
- `iran_national_id`
- `iran_economic_code`
- `iran_registration_number`
- `iran_postal_code`

## Supplier
- `iran_tax_section`
- `iran_national_id`
- `iran_economic_code`
- `iran_registration_number`
- `iran_postal_code`

These are stored in `custom_field.json`.

---

# Validation module

File:

`iran_localization/modules/core/validation.py`

Purpose:
- validate Iran postal code
- validate Iranian national ID field format
- validation must be optional via settings

Current validation logic includes:
- postal code: exactly 10 digits
- national ID: numeric, 10–11 digits

The module should use:

`enable_core_validation`

from `Iran Localization Settings`.

Do not make these fields mandatory.

---

# Iran Localization Settings

Custom Single DocType:

`Iran Localization Settings`

Module:

`Iran Localization`

It has System Manager permissions.

The DocType is stored in:

`iran_localization/fixtures/doctype.json`

Current fields expected in the fixture:

```text
enable_iran_validations
enable_official_invoice
enable_taxpayer_system
modules_section
enable_core_validation
enable_pricing_automation
enable_official_invoice_module
pricing_section
raw_material_price_list
selling_price_list
manufacturing_overhead_percent
profit_markup_percent
```

Current intended module switches:

- Core Validation
- Pricing Automation
- Official Invoice
- Taxpayer System integration later

The Iranian Taxpayer System must remain **optional** and must never block ordinary accounting, sales, or invoicing.

---

# Important current Settings issue

After fixture / migrate work, the structure of `Iran Localization Settings` was restored correctly, but site-specific values were reset.

At the last known working state, the values were manually restored through a fresh Bench Console transaction.

Expected pricing settings for the current dev site:

```text
enable_pricing_automation = 1
raw_material_price_list = قیمت مواد اولیه
selling_price_list = قیمت فروش محصولات
manufacturing_overhead_percent = 0
profit_markup_percent = 0
```

Do NOT hard-code these Price List names into the reusable plugin.

The plugin should only define the fields.

Each site should select its own Price Lists.

For a public plugin, defaults should be generic and site values should remain site-specific.

---

# Pricing module

File:

`iran_localization/modules/pricing/service.py`

This module is currently working for recursive BOM propagation when settings are valid.

The entry hook:

```python
update_product_prices_from_raw_material(doc, method=None)
```

Behavior:

1. Only runs when `enable_pricing_automation` is enabled.
2. Only reacts to `Item Price` changes in the configured raw-material Price List.
3. Finds BOMs that directly use the changed item.
4. Recalculates submitted BOM cost.
5. Reloads the BOM.
6. Updates or creates the finished product's `Item Price` in the configured selling Price List.
7. Recursively searches for parent BOMs that consume that finished item.
8. Continues propagation up the BOM tree.
9. Uses a `visited_boms` set to prevent loops.

The pricing calculation is currently conceptually:

```text
price = BOM total cost
price *= 1 + overhead_percent / 100
price *= 1 + profit_percent / 100
```

`frappe.utils.flt` is used to avoid string/number TypeErrors.

---

# Pricing test data

The current dev site contains test data.

## Raw material

```text
Item Code:
STEEL-ST37-TEST
```

Raw-material Price List:

```text
قیمت مواد اولیه
```

The raw material has an Item Price in that Price List.

---

## Direct product

```text
PRODUCT-TEST-001
```

Uses:

```text
STEEL-ST37-TEST
Qty = 2
```

Its BOM successfully updates when raw-material price changes.

---

## Multi-level test

Semi-finished product:

```text
SEMI-TEST-001
```

Its BOM uses:

```text
STEEL-ST37-TEST
Qty = 2
```

Final product:

```text
FINAL-TEST-001
```

Its BOM uses:

```text
SEMI-TEST-001
Qty = 1
```

Recursive propagation was tested successfully:

```text
STEEL-ST37-TEST
    ↓
SEMI-TEST-001
    ↓
FINAL-TEST-001
```

When the raw-material Item Price changed:
- SEMI BOM updated automatically
- FINAL BOM updated automatically
- Item Price for FINAL was created/updated automatically

No manual `Update Cost` was required after recursive logic was implemented.

---

# Price Lists

Current dev-site Price Lists:

## Raw materials

```text
قیمت مواد اولیه
```

Buying enabled.

## Product sales

```text
قیمت فروش محصولات
```

Selling enabled.

Again: these names are dev-site data, not plugin constants.

---

# BOM costing

For test BOMs, material rate is based on:

`Price List`

The raw-material Price List is used so manual raw-material price changes affect BOM cost.

Earlier, BOMs using Valuation Rate failed because no stock valuation existed for the test material.

---

# Git history / checkpoints

Multiple clean commits were created during development.

Recent logical checkpoints included:
- initial Iran company localization fields
- customer and supplier Iran fields
- validation
- configurable Iran localization settings
- automatic product pricing from raw-material cost
- recursive BOM price propagation

Before continuing major work, run:

```bash
cd /workspace/development/frappe-bench/apps/iran_localization
git status
git log --oneline --decorate -10
```

Do not assume the working tree is dirty or clean without checking.

---

# Design constraints for future Codex work

## Must preserve

- ERPNext core should remain untouched.
- `iran_localization` must stay installable as a standalone Frappe app.
- Features should be modular.
- Project-specific test items must not appear in production logic.
- Site-specific Price List names must not be hard-coded.
- Taxpayer System integration must remain optional.
- Normal ERP operations must continue if Taxpayer integration is disabled.
- Validation should be optional.
- Pricing automation should be optional.
- Future modules should have their own switch where appropriate.

---

# Recommended future module layout

Target direction:

```text
iran_localization/
└── iran_localization/
    ├── modules/
    │   ├── core/
    │   │   ├── validation.py
    │   │   └── settings.py
    │   │
    │   ├── pricing/
    │   │   ├── service.py
    │   │   ├── utils.py
    │   │   └── tests/
    │   │
    │   ├── official_invoice/
    │   │   ├── service.py
    │   │   ├── print_format/
    │   │   └── tests/
    │   │
    │   ├── taxpayer/
    │   │   ├── service.py
    │   │   ├── api.py
    │   │   └── tests/
    │   │
    │   └── sms/
    │       ├── service.py
    │       └── providers/
    │
    ├── fixtures/
    ├── patches/
    ├── hooks.py
    └── install.py
```

This is a target architecture, not necessarily the exact current tree.

---

# Immediate next tasks

Before adding more features, Codex should first stabilize the Settings system.

Recommended next sequence:

1. Inspect current:
   - `hooks.py`
   - `modules/pricing/service.py`
   - `modules/core/validation.py`
   - `fixtures/doctype.json`
   - `fixtures/custom_field.json`

2. Verify current Site settings survive:
   - normal Save from UI
   - `bench --site erp.localhost migrate`
   - Dev Container restart

3. Ensure `Iran Localization Settings` structure is fully stored in the app.

4. Ensure fixture import does **not** reset site-specific Single DocType values.

5. Add install/setup logic for safe defaults:
   - module switches
   - no hard-coded Price Lists

6. Add automated tests for:
   - pricing enabled
   - pricing disabled
   - direct BOM
   - multi-level BOM
   - existing selling Item Price
   - missing selling Item Price
   - cyclic / repeated BOM protection

7. Commit the stabilized modular version.

Only after that should new modules be added.

---

# Suggested next feature priorities

After stabilizing Settings:

1. Official Iranian invoice module
2. Persian invoice Print Format
3. Iran-specific company/customer/supplier fields cleanup
4. Better national ID validation
5. SMS notification abstraction
6. Website/API integration
7. Optional Taxpayer System integration
8. Packaging / README / semantic versioning
9. Automated tests
10. Public GitHub release

---

# Important note for Codex

Do not blindly rewrite the app.

First inspect the actual current repository state.

The conversation history included several temporary debugging steps that may already have been superseded by later fixes.

Use the repository as the source of truth.

Start by running:

```bash
cd /workspace/development/frappe-bench/apps/iran_localization

git status
git log --oneline --decorate -10
find iran_localization -maxdepth 4 -type f | sort
```

Then inspect the actual files before making changes.

The highest-priority task is:

**Make `Iran Localization Settings` reliable, modular, and migration-safe without resetting site-specific values.**

After that, preserve the already-working recursive pricing behavior.
