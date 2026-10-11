# Replaceable provider adapters

Providers live in installed Frappe apps. Administrator-selected keys resolve only through the registry;
settings cannot import arbitrary Python paths. To add a provider, register a class in your app's `hooks.py`:

```python
iran_sms_providers = ["your_app.sms.ExampleSMSProvider"]
iran_taxpayer_providers = ["your_app.tax.ExampleTaxProvider"]
```

The class implements:

```python
class ExampleTaxProvider:
    key = "example_tax"  # Unique across installed apps for this integration type.
    label = "Example Tax Provider"
    simulated = False

    def send(self, payload, idempotency_key, settings):
        # Read credentials with settings.get_password("taxpayer_api_key").
        # Validate/map the internal invoice into the provider's tax schema.
        # Verify current invoice pattern, tax identifiers, settlement and returns.
        # Sign/encrypt as required by that service, enforce bounded network timeouts.
        # Use idempotency_key if the provider supports it.
        return {"reference": "provider-confirmed-reference"}
```

SMS adapters receive `recipient` (normalized Iranian mobile number) and `message`.
Tax adapters receive schema version 1, invoice/date/currency, seller and buyer identity snapshots,
item tax identifiers and quantities, rates and net amounts, taxes/totals, return reference,
memory ID and provider key. Money is serialized as decimal strings from stored ERPNext values.
This is an internal integration payload, not the government wire format.

Raise `iran_localization.modules.integrations.service.ProviderRejected` only when rejection is confirmed
and no delivery occurred. Other exceptions become `Unknown`; raw exception messages are not persisted,
because they can expose credentials. Never put secrets in a payload or returned reference.

Set `simulated=True` only for a provider that performs no external delivery.
Do not map a simulated result to a real receipt. `Sent` describes provider acknowledgement, not tax approval.

Run `bench --site YOUR_SITE migrate` after installing a provider app; select its key in localization settings.
Switching keys affects newly queued requests. Pending/rejected requests require an explicit refresh action.
Provider configuration fingerprints prevent sending through a changed account without that refresh.

## HTTP taxpayer gateway v1

`http_gateway` bridges to a trusted custom gateway which implements the contract below.
It does not directly implement the government's changing transport/signing protocol.
The gateway owns provider-specific mapping, validation, signatures, keys and final tax receipts.

Request: POST to `taxpayer_endpoint` (HTTPS, redirects disabled).

```http
Authorization: Bearer <taxpayer_api_key>
Idempotency-Key: tax:<stable invoice hash>
Content-Type: application/json
```

```json
{
  "contract_version": 1,
  "idempotency_key": "tax:<stable invoice hash>",
  "invoice": {
    "schema_version": 1,
    "invoice": "YOUR_INVOICE",
    "posting_date": "2026-10-06",
    "currency": "IRR",
    "memory_id": "YOUR_MEMORY_ID",
    "company": {"name": "YOUR_COMPANY", "national_id": "..."},
    "customer": {"name": "YOUR_CUSTOMER", "national_id": "..."},
    "items": [],
    "taxes": [],
    "net_total": "1000.0",
    "tax_total": "0.0",
    "grand_total": "1000.0",
    "rounded_total": "1000.0",
    "is_return": false,
    "return_against": null,
    "provider": "http_gateway"
  }
}
```

Success response (2xx): `{"accepted": true, "reference": "gateway-receipt"}`.
Confirmed rejection (2xx): `{"accepted": false}`.
A missing/nonboolean acceptance or missing reference is an unknown outcome. HTTP errors are conservatively
unknown because an upstream service could already have accepted the request.
Use provider reconciliation before retrying an unknown outcome. The gateway must retain idempotency receipts
and return the same receipt for repeated keys, including across network timeouts.

The app does not automatically poll final tax status. Check the provider receipt using the gateway's own
status interface, or extend this adapter with your selected provider's documented status flow.
Before live use, exercise sandbox invoices, returns, rejection, timeout and receipt reconciliation with that provider.
