"""Authenticated headless commerce API using ERPNext prices and document permissions."""

import hashlib
import json
import math
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, today

from iran_localization.modules.core.settings import get_settings


def _settings():
	frappe.only_for(["Sales User", "Sales Manager", "System Manager"])
	settings = get_settings()
	if not settings.enable_commerce_api:
		frappe.throw(_("The commerce API is disabled."))
	if not all((settings.commerce_price_list, settings.commerce_company, settings.commerce_customer)):
		frappe.throw(_("Complete commerce settings first."))
	return settings


@frappe.whitelist()
def catalog(start=0, page_length=20):
	settings = _settings()
	start, page_length = max(cint(start), 0), min(max(cint(page_length), 1), 100)
	items = frappe.get_list(
		"Item",
		filters={"iran_publish_to_commerce": 1, "disabled": 0, "is_sales_item": 1, "has_variants": 0},
		fields=["item_code", "item_name", "stock_uom", "image"],
		start=start,
		page_length=page_length,
		order_by="item_code asc",
	)
	for item in items:
		prices = frappe.get_list(
			"Item Price",
			filters={"item_code": item.item_code, "price_list": settings.commerce_price_list},
			fields=[
				"price_list_rate",
				"currency",
				"uom",
				"customer",
				"supplier",
				"batch_no",
				"valid_from",
				"valid_upto",
				"packing_unit",
			],
			page_length=0,
			order_by="valid_from desc, name asc",
		)
		date = getdate(today())
		price = next(
			(
				row
				for row in prices
				if not any(row.get(key) for key in ("supplier", "batch_no"))
				and row.customer in (None, "", settings.commerce_customer)
				and row.uom in (None, "", item.stock_uom)
				and flt(row.packing_unit) <= 1
				and (not row.valid_from or getdate(row.valid_from) <= date)
				and (not row.valid_upto or getdate(row.valid_upto) >= date)
			),
			None,
		)
		item["price"] = price.price_list_rate if price else None
		item["currency"] = price.currency if price else None
	return {"items": items, "start": start, "page_length": page_length}


def _order(settings, items, delivery_date):
	if isinstance(items, str):
		items = frappe.parse_json(items)
	if not isinstance(items, list) or not 1 <= len(items) <= 100:
		frappe.throw(_("Provide 1–100 order lines."))
	if getdate(delivery_date) < getdate(today()):
		frappe.throw(_("Delivery date cannot be in the past."))
	doc = frappe.new_doc("Sales Order")
	doc.check_permission("create")
	doc.update(
		{
			"customer": settings.commerce_customer,
			"company": settings.commerce_company,
			"selling_price_list": settings.commerce_price_list,
			"delivery_date": delivery_date,
			"transaction_date": today(),
			"order_type": "Sales",
		}
	)
	for row in items:
		if not isinstance(row, dict) or set(row) - {"item_code", "qty"}:
			frappe.throw(_("Order lines accept only item_code and qty."))
		qty = flt(row.get("qty"))
		if not math.isfinite(qty) or qty <= 0 or qty > 1000000:
			frappe.throw(_("Order quantity must be positive and at most 1,000,000."))
		item = frappe.get_doc("Item", row.get("item_code"))
		item.check_permission("read")
		if not item.iran_publish_to_commerce or item.disabled or not item.is_sales_item or item.has_variants:
			frappe.throw(_("Item is not available in the commerce catalog."))
		doc.append("items", {"item_code": item.name, "qty": qty, "delivery_date": delivery_date})
	# New child rows default rates to zero. None tells ERPNext to fetch configured prices.
	for row in doc.items:
		row.rate = None
		row.price_list_rate = None
	doc.set_missing_values()
	doc.calculate_taxes_and_totals()
	for row in doc.items:
		if flt(row.rate) <= 0:
			frappe.throw(_("No positive selling price is available for {0}.").format(row.item_code))
	return doc


def _summary(doc):
	return {
		"name": doc.name if not doc.is_new() else None,
		"currency": doc.currency,
		"net_total": doc.net_total,
		"tax_total": doc.total_taxes_and_charges,
		"grand_total": doc.grand_total,
		"items": [
			{"item_code": row.item_code, "qty": row.qty, "rate": row.rate, "amount": row.amount}
			for row in doc.items
		],
	}


@frappe.whitelist(methods=["POST"])
def quote(items, delivery_date):
	return _summary(_order(_settings(), items, delivery_date))


@frappe.whitelist(methods=["POST"])
def create_order(items, delivery_date, request_id):
	settings = _settings()
	if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", request_id):
		frappe.throw(_("Provide a unique request ID with 8–80 letters, digits, underscores or hyphens."))
	# Scope idempotency to the authenticated account, so another user cannot retrieve its order.
	key = hashlib.sha256((frappe.session.user + ":" + request_id).encode()).hexdigest()
	parsed_items = frappe.parse_json(items) if isinstance(items, str) else items
	payload_hash = hashlib.sha256(
		json.dumps(
			{"items": parsed_items, "delivery_date": str(getdate(delivery_date))}, sort_keys=True
		).encode()
	).hexdigest()
	existing = frappe.db.get_value("Sales Order", {"iran_commerce_request_id": key}, "name")
	if existing:
		doc = frappe.get_doc("Sales Order", existing)
		doc.check_permission("read")
		if doc.iran_commerce_payload_hash != payload_hash:
			frappe.throw(_("This request ID has already been used for a different order."))
		return _summary(doc)
	doc = _order(settings, items, delivery_date)
	doc.iran_commerce_request_id = key
	doc.iran_commerce_payload_hash = payload_hash
	doc.insert()
	return _summary(doc)
