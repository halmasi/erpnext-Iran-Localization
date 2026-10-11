import frappe
from frappe import _
from frappe.utils import getdate

from iran_localization.modules.core.settings import get_settings

IDENTITY_FIELDS = ("national_id", "economic_code", "registration_number", "postal_code")


def jalali_date(value):
	import jdatetime

	return jdatetime.date.fromgregorian(date=getdate(value)).strftime("%Y/%m/%d")


def _party(doctype, name, invoice, prefix):
	party = frappe.get_doc(doctype, name)
	result = {"name": name, "display_name": party.get("company_name") or party.get("customer_name") or name}
	for key in IDENTITY_FIELDS:
		snapshot = invoice.get(f"iran_{prefix}_{key}")
		# Official submitted invoices use their saved snapshot, including empty values.
		result[key] = snapshot if invoice.get("iran_official_invoice") else party.get("iran_" + key)
	return result


def invoice_context(invoice):
	if isinstance(invoice, str):
		invoice = frappe.get_doc("Sales Invoice", invoice)
	return {
		"jalali_date": jalali_date(invoice.posting_date),
		"seller": _party("Company", invoice.company, invoice, "seller"),
		"buyer": _party("Customer", invoice.customer, invoice, "buyer"),
	}


def validate_invoice(doc, method=None):
	if not doc.get("iran_official_invoice") or doc.docstatus == 2:
		return
	if not get_settings().enable_official_invoice_module:
		frappe.throw(_("Enable the official invoice module before marking an invoice as official."))
	previous = doc.get_doc_before_save()
	if doc.docstatus == 0 or doc.is_new() or (previous and previous.docstatus == 0 and doc.docstatus == 1):
		for prefix, doctype, name in (
			("seller", "Company", doc.company),
			("buyer", "Customer", doc.customer),
		):
			party = frappe.get_doc(doctype, name)
			for key in IDENTITY_FIELDS:
				doc.set(f"iran_{prefix}_{key}", party.get("iran_" + key))
			if not party.get("iran_national_id") or not party.get("iran_postal_code"):
				frappe.throw(
					_("National ID and postal code are required for an official invoice: {0}").format(name)
				)


@frappe.whitelist()
def module_status():
	settings = get_settings()
	return {
		key: bool(settings.get(key))
		for key in (
			"enable_official_invoice_module",
			"enable_taxpayer_system",
			"enable_sms",
			"enable_commerce_api",
		)
	}
