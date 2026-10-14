"""Use the configured selling list in ERPNext's item-selection pipeline."""

import frappe
from frappe.utils import today

from iran_localization.modules.core.settings import get_settings


class SalesInvoicePricingMixin:
	@frappe.whitelist()
	def process_item_selection(self, item_idx, reset_item_details=False):
		configured = get_settings().selling_price_list
		if configured and self.selling_price_list in (None, "", "Standard Selling"):
			price_list = frappe.get_cached_doc("Price List", configured)
			if price_list.enabled and price_list.selling:
				self.selling_price_list = configured
				self.price_list_currency = price_list.currency
		result = super().process_item_selection(item_idx, reset_item_details)
		item = self.get("items", {"idx": item_idx})[0]
		if not item.rate:
			customer = self.get("customer")
			if self.doctype == "Quotation" and self.get("quotation_to") == "Customer":
				customer = self.get("party_name")
			date = self.get("posting_date") or self.get("transaction_date") or today()
			prices = frappe.get_all("Item Price", filters={
				"item_code": item.item_code, "price_list": self.selling_price_list,
				"customer": ["in", ["", customer or ""]],
			}, fields=["uom", "valid_from", "valid_upto"])
			units = frappe.get_all("UOM Conversion Detail", filters={"parent": item.item_code}, pluck="uom")
			valid_units = {p.uom for p in prices if p.uom in units
				and (not p.valid_from or str(p.valid_from) <= str(date))
				and (not p.valid_upto or str(p.valid_upto) >= str(date))}
			if len(valid_units) == 1:
				item.uom = valid_units.pop()
				result = super().process_item_selection(item_idx, False)
		return result
