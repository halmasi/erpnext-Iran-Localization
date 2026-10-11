"""Auditable integration requests with explicit dispatch and no automatic retry."""

import hashlib
import json

import frappe
from frappe import _
from frappe.utils import cint

from iran_localization.modules.core.settings import get_settings
from iran_localization.modules.integrations.registry import get_provider


class ProviderRejected(Exception):
	"""Provider explicitly confirmed it did not accept the request."""


def provider_fingerprint(kind, key, settings):
	password = getattr(settings, "get_password", None)
	secret = password(f"{kind}_api_key", raise_exception=False) if password else None
	configuration = {
		"key": key,
		"secret": secret,
		"sender": settings.get("sms_sender") if kind == "sms" else None,
		"endpoint": settings.get("taxpayer_endpoint") if kind == "taxpayer" else None,
		"memory_id": settings.get("taxpayer_memory_id") if kind == "taxpayer" else None,
		"company": settings.get("taxpayer_company") if kind == "taxpayer" else None,
	}
	return hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()


def _save_request(request):
	request.flags.iran_integration_update = True
	request.save(ignore_permissions=True)


def create_request(kind, payload, idempotency_key, reference=None):
	settings = get_settings()
	switch = "enable_sms" if kind == "sms" else "enable_taxpayer_system"
	if not cint(settings.get(switch)):
		frappe.throw(_("This integration is disabled."))
	key = settings.get(f"{kind}_provider")
	get_provider(kind, key)
	existing = frappe.db.get_value("Iran Integration Request", {"idempotency_key": idempotency_key}, "name")
	if existing:
		request = frappe.get_doc("Iran Integration Request", existing)
		if (
			request.provider != key
			or request.integration != ("SMS" if kind == "sms" else "Taxpayer")
			or json.loads(request.payload) != payload
		):
			frappe.throw(_("This request ID has already been used for a different payload or provider."))
		return request
	request = frappe.get_doc(
		{
			"doctype": "Iran Integration Request",
			"integration": "SMS" if kind == "sms" else "Taxpayer",
			"provider": key,
			"provider_config_fingerprint": provider_fingerprint(kind, key, settings),
			"idempotency_key": idempotency_key,
			"payload": json.dumps(payload, ensure_ascii=False, sort_keys=True),
		}
	)
	if reference:
		request.reference_doctype, request.reference_name = reference
	return request.insert(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def dispatch(name):
	frappe.only_for("System Manager")
	request = frappe.get_doc("Iran Integration Request", name, for_update=True)
	if request.status != "Pending":
		return {"name": request.name, "status": request.status}
	kind = "sms" if request.integration == "SMS" else "taxpayer"
	settings = get_settings()
	switch = "enable_sms" if kind == "sms" else "enable_taxpayer_system"
	if not settings.get(switch):
		frappe.throw(_("This integration is disabled."))
	# Switching provider must not accidentally send an old request through a new account.
	if request.provider != settings.get(f"{kind}_provider"):
		frappe.throw(_("This request belongs to a different provider. Create a new request."))
	if request.provider_config_fingerprint != provider_fingerprint(kind, request.provider, settings):
		frappe.throw(_("Provider account settings have changed since this request was queued."))
	if request.reference_doctype:
		reference = frappe.get_doc(request.reference_doctype, request.reference_name)
		reference.check_permission("read")
		if kind == "taxpayer" and reference.docstatus != 1:
			frappe.throw(_("Only submitted invoices can be sent."))
	provider = get_provider(kind, request.provider)
	request.status = "Processing"
	request.attempts = cint(request.attempts) + 1
	_save_request(request)
	# Persist before network I/O. A crash leaves Processing for manual reconciliation,
	# rather than allowing a duplicate send after a transaction rollback.
	frappe.db.commit()
	try:
		result = provider.send(json.loads(request.payload), request.idempotency_key, settings)
		request.provider_reference = result["reference"]
		request.status = "Simulated" if provider.simulated else "Sent"
		request.error = None
	except ProviderRejected:
		request.status = "Failed"
		request.error = "Provider rejected the request. Check provider configuration."
	except Exception:
		# Provider exceptions can contain credential-bearing URLs: never persist them.
		request.status = "Unknown"
		request.error = "Delivery outcome is unknown. Reconcile with the provider before sending again."
	_save_request(request)
	return {"name": request.name, "status": request.status, "reference": request.provider_reference}


@frappe.whitelist(methods=["POST"])
def retry_request(name):
	frappe.only_for("System Manager")
	request = frappe.get_doc("Iran Integration Request", name, for_update=True)
	if request.status != "Failed":
		frappe.throw(_("Only confirmed failed requests may be retried."))
	request.status = "Pending"
	request.error = None
	_save_request(request)
	return {"name": request.name, "status": request.status}


@frappe.whitelist(methods=["POST"])
def refresh_provider(name):
	"""Explicitly refresh an unsent or confirmed-rejected request after provider changes."""
	frappe.only_for("System Manager")
	request = frappe.get_doc("Iran Integration Request", name, for_update=True)
	if request.status not in ("Pending", "Failed"):
		frappe.throw(_("Only pending or confirmed failed requests may change provider."))
	kind = "sms" if request.integration == "SMS" else "taxpayer"
	settings = get_settings()
	if not settings.get("enable_sms" if kind == "sms" else "enable_taxpayer_system"):
		frappe.throw(_("This integration is disabled."))
	get_provider(kind, settings.get(f"{kind}_provider"))
	if kind == "taxpayer":
		from iran_localization.modules.taxpayer.service import prepare_payload

		invoice = frappe.get_doc(request.reference_doctype, request.reference_name)
		invoice.check_permission("read")
		request.payload = json.dumps(prepare_payload(invoice, settings), ensure_ascii=False, sort_keys=True)
	request.provider = settings.get(f"{kind}_provider")
	request.provider_config_fingerprint = provider_fingerprint(kind, request.provider, settings)
	request.flags.iran_integration_reconfigure = True
	request.status = "Pending"
	request.error = None
	_save_request(request)
	return {"name": request.name, "status": request.status}


@frappe.whitelist(methods=["POST"])
def reconcile(name, accepted, provider_reference=None):
	"""Explicit operator reconciliation after checking the external provider."""
	frappe.only_for("System Manager")
	request = frappe.get_doc("Iran Integration Request", name, for_update=True)
	if request.status not in ("Processing", "Unknown"):
		frappe.throw(_("Only requests with unknown delivery outcomes need reconciliation."))
	accepted = cint(accepted)
	if accepted and not provider_reference:
		frappe.throw(_("Enter the reference confirmed by the provider."))
	request.status = "Sent" if accepted else "Failed"
	request.provider_reference = provider_reference or None
	request.error = "Manually reconciled by " + frappe.session.user
	_save_request(request)
	return {"name": request.name, "status": request.status}
