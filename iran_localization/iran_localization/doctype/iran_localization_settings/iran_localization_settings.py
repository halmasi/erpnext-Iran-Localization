import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class IranLocalizationSettings(Document):
	def on_update(self):
		from iran_localization.modules.core.language import apply_language_settings

		apply_language_settings(self)

	def validate(self):
		if self.enable_pricing_automation:
			if not self.raw_material_price_list or not self.selling_price_list:
				frappe.throw(_("Select raw material and selling Price Lists before enabling pricing."))
			if self.raw_material_price_list == self.selling_price_list:
				frappe.throw(_("Raw material and selling Price Lists must be different."))
			if not frappe.db.get_value("Price List", self.raw_material_price_list, "buying"):
				frappe.throw(_("The raw material Price List must allow buying."))
			if not frappe.db.get_value("Price List", self.selling_price_list, "selling"):
				frappe.throw(_("The selling Price List must allow selling."))
		for key in ("manufacturing_overhead_percent", "profit_markup_percent"):
			if flt(self.get(key)) < 0:
				frappe.throw(_("Overhead and markup must not be negative."))
		from iran_localization.modules.integrations.registry import get_provider

		for enabled, kind, key in (
			(self.enable_sms, "sms", self.sms_provider),
			(self.enable_taxpayer_system, "taxpayer", self.taxpayer_provider),
		):
			if enabled:
				get_provider(kind, key)
		if (
			self.enable_sms
			and self.sms_provider == "kavenegar"
			and (not self.sms_api_key or not self.sms_sender)
		):
			frappe.throw(_("Set the SMS API key and sender before enabling Kavenegar."))
		if self.enable_taxpayer_system and self.taxpayer_provider == "http_gateway":
			from urllib.parse import urlsplit

			parsed = urlsplit(self.taxpayer_endpoint or "")
			if (
				parsed.scheme != "https"
				or not parsed.hostname
				or parsed.username
				or parsed.password
				or parsed.fragment
			):
				frappe.throw(_("Use an HTTPS taxpayer endpoint without embedded credentials."))
			if not self.taxpayer_api_key or not self.taxpayer_memory_id or not self.taxpayer_company:
				frappe.throw(
					_("Set the taxpayer API key, company and tax memory ID before enabling the gateway.")
				)
		if self.enable_commerce_api:
			if not all((self.commerce_price_list, self.commerce_customer, self.commerce_company)):
				frappe.throw(_("Select commerce Price List, customer and company before enabling the API."))
			if not frappe.db.get_value("Price List", self.commerce_price_list, "selling"):
				frappe.throw(_("The commerce Price List must allow selling."))
