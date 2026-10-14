"""Update affected BOMs in dependency order, then publish unit selling prices."""

from graphlib import CycleError, TopologicalSorter

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from iran_localization.modules.core.settings import get_settings


@frappe.whitelist()
def get_sales_item_price(item_code, price_list=None, uom=None):
	"""Return the current selling price used by the invoice item picker."""
	if not item_code:
		return None
	rows = frappe.db.sql(
		"""select ip.price_list_rate, ip.valid_from, ip.valid_upto, ip.uom
		from `tabItem Price` ip join `tabPrice List` pl on pl.name = ip.price_list
		where ip.item_code=%s and pl.selling=1
		and (%s is null or %s='' or ip.price_list=%s)
		and (%s is null or %s='' or ip.uom=%s or ip.uom='')
		order by (ip.price_list=%s) desc, ip.valid_from desc, (ip.uom=%s) desc""",
		(item_code, price_list, price_list, price_list, uom, uom, uom, price_list, uom),
		as_dict=True,
	)
	if not rows and price_list:
		return get_sales_item_price(item_code, None, uom)
	date = getdate(today())
	for row in rows:
		if row.valid_from and getdate(row.valid_from) > date:
			continue
		if row.valid_upto and getdate(row.valid_upto) < date:
			continue
		return row.price_list_rate
	return None


def fill_missing_sales_invoice_rates(doc, method=None):
	"""Fill an empty invoice-row rate from the invoice's active Item Price."""
	if doc.doctype != "Sales Invoice" or not doc.get("selling_price_list"):
		return
	for row in doc.get("items") or []:
		if not row.item_code or flt(row.rate):
			continue
		filters = {"item_code": row.item_code, "price_list": doc.selling_price_list}
		if row.uom:
			filters["uom"] = ["in", [row.uom, ""]]
		prices = frappe.get_all("Item Price", filters=filters, fields=["price_list_rate", "valid_from", "valid_upto", "uom"], order_by="valid_from desc, uom desc")
		if not prices:
			# A legacy invoice may retain Standard Selling while the active selling
			# list was renamed. Use a matching active selling list as a safe fallback.
			prices = frappe.db.sql(
				"""select ip.price_list_rate, ip.valid_from, ip.valid_upto, ip.uom
				from `tabItem Price` ip join `tabPrice List` pl on pl.name = ip.price_list
				where ip.item_code=%s and pl.selling=1
				order by ip.valid_from desc, ip.uom desc""",
				(row.item_code,), as_dict=True,
			)
		date = getdate(today())
		for price in prices:
			if price.valid_from and getdate(price.valid_from) > date:
				continue
			if price.valid_upto and getdate(price.valid_upto) < date:
				continue
			row.rate = price.price_list_rate
			row.price_list_rate = price.price_list_rate
			break


def update_product_prices_from_raw_material(doc, method=None):
	if frappe.flags.iran_pricing_running:
		return
	settings = get_settings()
	if not settings.enable_pricing_automation:
		return
	if not settings.raw_material_price_list:
		return
	if doc.price_list != settings.raw_material_price_list:
		return
	if settings.update_selling_price_automatically:
		if not settings.selling_price_list:
			frappe.throw(
				_("A selling Price List is required when automatic selling price updates are enabled.")
			)
		if settings.raw_material_price_list == settings.selling_price_list:
			frappe.throw(_("Raw material and selling Price Lists must be different."))

	frappe.flags.iran_pricing_running = True
	try:
		_update_dependent_boms_and_prices(doc.item_code, settings, set())
	finally:
		frappe.flags.iran_pricing_running = False


def _dependent_boms(item_code):
	names = frappe.get_all(
		"BOM Item", filters={"item_code": item_code, "parenttype": "BOM"}, pluck="parent", distinct=True
	)
	if not names:
		return []
	return frappe.get_all(
		"BOM",
		filters={"name": ["in", names], "docstatus": 1, "is_active": 1},
		fields=["name", "item", "is_default"],
		order_by="name asc",
	)


def _collect_graph(item_code):
	nodes, graph, pending, seen_items = {}, {}, [item_code], set()
	while pending:
		item = pending.pop()
		if item in seen_items:
			continue
		seen_items.add(item)
		for row in _dependent_boms(item):
			nodes[row.name] = row
			graph.setdefault(row.name, set())
			pending.append(row.item)
	for child in nodes.values():
		for parent in _dependent_boms(child.item):
			if parent.name in nodes:
				graph[parent.name].add(child.name)
	try:
		return nodes, list(TopologicalSorter(graph).static_order())
	except CycleError:
		frappe.throw(_("A cyclic BOM dependency prevents automatic pricing."))


def _update_dependent_boms_and_prices(item_code, settings, visited_boms):
	nodes, order = _collect_graph(item_code)
	for name in order:
		if name in visited_boms:
			continue
		visited_boms.add(name)
		bom = frappe.get_doc("BOM", name)
		bom.update_cost(update_parent=False)
		bom.reload()
		if not settings.update_selling_price_automatically:
			continue
		if not nodes[name].is_default:
			continue
		if flt(bom.quantity) <= 0:
			frappe.throw(_("BOM output quantity must be positive."))
		price_currency = frappe.db.get_value("Price List", settings.selling_price_list, "currency")
		base_cost = flt(bom.total_cost) / flt(bom.quantity)
		if bom.currency != price_currency:
			from erpnext.setup.utils import get_exchange_rate

			rate = get_exchange_rate(bom.currency, price_currency, args="for_selling")
			if not rate:
				frappe.throw(_("A currency exchange rate is required for automatic pricing."))
			base_cost *= flt(rate)
		_update_selling_price(bom.item, base_cost, settings, uom=bom.uom)


def _update_selling_price(item_code, base_cost, settings, uom=None):
	price = flt(base_cost)
	price *= 1 + flt(settings.manufacturing_overhead_percent) / 100
	price *= 1 + flt(settings.profit_markup_percent) / 100
	if not uom:
		uom = frappe.db.get_value("Item", item_code, "stock_uom")
	matches = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "price_list": settings.selling_price_list, "uom": uom},
		fields=["name", "customer", "supplier", "batch_no", "valid_from", "valid_upto", "packing_unit"],
	)
	date = getdate(today())
	generic = [
		row
		for row in matches
		if not any(row.get(key) for key in ("customer", "supplier", "batch_no"))
		and flt(row.packing_unit) <= 1
		and (not row.valid_from or getdate(row.valid_from) <= date)
		and (not row.valid_upto or getdate(row.valid_upto) >= date)
	]
	generic.sort(key=lambda row: getdate(row.valid_from or "1900-01-01"), reverse=True)
	if len(generic) > 1 and generic[0].valid_from == generic[1].valid_from:
		frappe.throw(_("Multiple generic selling prices exist for item {0}.").format(item_code))
	if generic:
		item_price = frappe.get_doc("Item Price", generic[0].name)
		item_price.price_list_rate = flt(price, item_price.precision("price_list_rate"))
		item_price.save(ignore_permissions=True)
	else:
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": settings.selling_price_list,
				"uom": uom,
				"price_list_rate": price,
			}
		)
		item_price.price_list_rate = flt(price, item_price.precision("price_list_rate"))
		item_price.insert(ignore_permissions=True)
