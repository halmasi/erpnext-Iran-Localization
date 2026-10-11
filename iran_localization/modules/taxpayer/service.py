import hashlib
import json

import frappe
from frappe import _

from iran_localization.modules.core.settings import get_settings
from iran_localization.modules.integrations.registry import get_provider
from iran_localization.modules.integrations.service import create_request
from iran_localization.modules.official_invoice.service import invoice_context


def invoice_payload(invoice):
	"""Internal adapter contract; providers map/sign it to their own tax API schema."""
	context = invoice_context(invoice)
	return {
		"schema_version": 1,
		"invoice": invoice.name,
		"posting_date": str(invoice.posting_date),
		"currency": invoice.currency,
		"company": context["seller"],
		"customer": context["buyer"],
		"is_return": bool(invoice.is_return),
		"return_against": invoice.return_against,
		"items": [
			{
				"item_code": row.item_code,
				"tax_id": frappe.db.get_value("Item", row.item_code, "iran_tax_item_id"),
				"qty": str(row.qty),
				"uom": row.uom,
				"rate": str(row.rate),
				"net_amount": str(row.net_amount),
			}
			for row in invoice.items
		],
		"net_total": str(invoice.net_total),
		"tax_total": str(invoice.total_taxes_and_charges),
		"grand_total": str(invoice.grand_total),
		"rounded_total": str(invoice.rounded_total),
		"taxes": [
			{"description": row.description, "amount": str(row.tax_amount), "rate": str(row.rate)}
			for row in invoice.taxes
		],
	}


@frappe.whitelist(methods=["POST"])
def queue_invoice(name):
	frappe.only_for("System Manager")
	invoice = frappe.get_doc("Sales Invoice", name)
	invoice.check_permission("read")
	settings = get_settings()
	payload = prepare_payload(invoice, settings)
	# The invoice identity remains unique even if settings or provider are changed later.
	digest = hashlib.sha256(invoice.name.encode()).hexdigest()
	request = create_request("taxpayer", payload, "tax:" + digest, ("Sales Invoice", name))
	return {"name": request.name, "status": request.status}


def prepare_payload(invoice, settings):
	if invoice.docstatus != 1:
		frappe.throw(_("Only submitted invoices can be queued."))
	payload = invoice_payload(invoice)
	payload["memory_id"] = settings.taxpayer_memory_id
	payload["provider"] = settings.taxpayer_provider
	provider = get_provider("taxpayer", settings.taxpayer_provider)
	if not provider.simulated:
		if invoice.company != settings.taxpayer_company or not settings.taxpayer_memory_id:
			frappe.throw(_("Select the taxpayer company and its tax memory ID before sending."))
		if not all(row["tax_id"] for row in payload["items"]):
			frappe.throw(_("Set a tax item ID for every invoice item before sending."))
		if not payload["company"].get("national_id") or not payload["customer"].get("national_id"):
			frappe.throw(_("Seller and buyer national IDs are required for tax submission."))
	return payload
