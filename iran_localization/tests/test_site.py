"""Database integration tests; use an isolated test site and roll back each case."""

import unittest
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.utils import add_days, today

from iran_localization.modules.commerce import api
from iran_localization.modules.core.settings import initialize_defaults
from iran_localization.modules.integrations.service import dispatch
from iran_localization.modules.official_invoice.service import invoice_context, jalali_date
from iran_localization.modules.sms.service import queue_sms


class TestSite(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.savepoint = "iran_test_" + uuid4().hex
		frappe.db.savepoint(self.savepoint)
		self.addCleanup(self.cleanup)
		self.prefix = "IL-" + uuid4().hex[:10]
		companies = frappe.get_all("Company", fields=["name", "default_currency"], limit=1)
		if not companies:
			self.skipTest("Create a test Company with its chart of accounts before running site tests.")
		self.company = companies[0].name
		self.currency = companies[0].default_currency
		self.settings = frappe.get_single("Iran Localization Settings")
		self.settings.enable_pricing_automation = 0
		self.settings.enable_core_validation = 0
		self.settings.save()
		self.raw_list = self.price_list("Raw", buying=1)
		self.sales_list = self.price_list("Sales", selling=1)
		self.uom = frappe.db.get_value("UOM", "Nos", "name") or frappe.db.get_value("UOM", {}, "name")
		self.group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
		if not self.group:
			self.group = (
				frappe.get_doc(
					{
						"doctype": "Item Group",
						"item_group_name": self.prefix,
						"parent_item_group": "All Item Groups",
					}
				)
				.insert()
				.name
			)

	def cleanup(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point=self.savepoint)
		frappe.clear_document_cache("Iran Localization Settings", "Iran Localization Settings")
		frappe.flags.iran_pricing_running = False

	def price_list(self, suffix, **kw):
		return (
			frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": self.prefix + suffix,
					"currency": self.currency,
					"enabled": 1,
					**kw,
				}
			)
			.insert()
			.name
		)

	def item(self, suffix):
		return (
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": self.prefix + suffix,
					"item_name": suffix,
					"stock_uom": self.uom,
					"item_group": self.group,
					"iran_publish_to_commerce": 1,
					"is_stock_item": 1,
				}
			)
			.insert()
			.name
		)

	def item_price(self, item, rate, price_list):
		return frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item,
				"price_list": price_list,
				"price_list_rate": rate,
				"uom": self.uom,
			}
		).insert()

	def bom(self, item, components, quantity=1):
		doc = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item,
				"company": self.company,
				"currency": self.currency,
				"quantity": quantity,
				"is_active": 1,
				"is_default": 1,
				"rm_cost_as_per": "Price List",
				"buying_price_list": self.raw_list,
				"items": components,
			}
		)
		doc.insert()
		doc.submit()
		return doc

	def enable_pricing(self):
		self.settings.raw_material_price_list = self.raw_list
		self.settings.selling_price_list = self.sales_list
		self.settings.enable_pricing_automation = 1
		self.settings.update_selling_price_automatically = 1
		self.settings.manufacturing_overhead_percent = 0
		self.settings.profit_markup_percent = 0
		self.settings.save()

	def customer(self):
		return (
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": self.prefix + "Buyer",
					"customer_type": "Company",
					"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
					"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name")
					or "All Territories",
					"iran_national_id": "10380284790",
					"iran_postal_code": "1234567890",
				}
			)
			.insert()
			.name
		)

	def test_quotation_item_selection_uses_configured_selling_price(self):
		item = self.item("Quoted")
		self.item_price(item, 6400000, self.sales_list)
		self.settings.selling_price_list = self.sales_list
		self.settings.save()
		doc = frappe.new_doc("Quotation")
		doc.company = self.company
		doc.quotation_to = "Customer"
		doc.party_name = self.customer()
		doc.currency = self.currency
		doc.conversion_rate = 1
		doc.selling_price_list = "Standard Selling"
		doc.append("items", {"item_code": item, "qty": 2})
		doc.process_item_selection(1, True)
		self.assertEqual(doc.selling_price_list, self.sales_list)
		self.assertEqual(doc.items[0].rate, 6400000)
		self.assertEqual(doc.items[0].amount, 12800000)

	def test_saved_settings_survive_forced_schema_import(self):
		from frappe.modules.import_file import import_file_by_path

		self.settings.raw_material_price_list = self.raw_list
		self.settings.enable_core_validation = 0
		self.settings.manufacturing_overhead_percent = 7.5
		self.settings.sms_api_key = "test-only-secret-" + self.prefix
		self.settings.save()
		before = frappe.db.get_singles_dict("Iran Localization Settings")
		path = frappe.get_app_path(
			"iran_localization",
			"iran_localization",
			"doctype",
			"iran_localization_settings",
			"iran_localization_settings.json",
		)
		import_file_by_path(path, force=True)
		initialize_defaults()
		after = frappe.db.get_singles_dict("Iran Localization Settings")
		for key in ("raw_material_price_list", "enable_core_validation", "manufacturing_overhead_percent"):
			self.assertEqual(before[key], after[key])
		self.assertEqual(
			frappe.get_single("Iran Localization Settings").get_password("sms_api_key"),
			"test-only-secret-" + self.prefix,
		)

	def test_direct_price_updates_existing_row(self):
		raw, product = self.item("Raw"), self.item("Product")
		price = self.item_price(raw, 100, self.raw_list)
		self.bom(product, [{"item_code": raw, "qty": 2}])
		selling = self.item_price(product, 200, self.sales_list)
		self.enable_pricing()
		price.price_list_rate = 300
		price.save()
		selling.reload()
		self.assertEqual(selling.price_list_rate, 600)
		self.assertEqual(
			frappe.db.count("Item Price", {"item_code": product, "price_list": self.sales_list}), 1
		)

	def test_multilevel_and_batch_quantity(self):
		raw, semi, final = self.item("Raw"), self.item("Semi"), self.item("Final")
		price = self.item_price(raw, 100, self.raw_list)
		semi_bom = self.bom(semi, [{"item_code": raw, "qty": 2}])
		final_bom = self.bom(final, [{"item_code": semi, "qty": 3, "bom_no": semi_bom.name}], quantity=2)
		self.enable_pricing()
		price.price_list_rate = 200
		price.save()
		final_bom.reload()
		self.assertEqual(final_bom.total_cost, 1200)
		self.assertEqual(
			frappe.db.get_value(
				"Item Price", {"item_code": final, "price_list": self.sales_list}, "price_list_rate"
			),
			600,
		)
		price.price_list_rate = 300
		price.save()
		self.assertEqual(
			frappe.db.count("Item Price", {"item_code": final, "price_list": self.sales_list}), 1
		)

	def test_diamond_propagation_uses_both_new_child_costs(self):
		raw, a, b, final = [self.item(suffix) for suffix in ("Raw", "A", "B", "Final")]
		price = self.item_price(raw, 100, self.raw_list)
		bom_a = self.bom(a, [{"item_code": raw, "qty": 2}])
		bom_b = self.bom(b, [{"item_code": raw, "qty": 3}])
		bom_final = self.bom(
			final,
			[
				{"item_code": a, "qty": 1, "bom_no": bom_a.name},
				{"item_code": b, "qty": 1, "bom_no": bom_b.name},
			],
		)
		self.enable_pricing()
		price.price_list_rate = 200
		price.save()
		bom_final.reload()
		self.assertEqual(bom_final.total_cost, 1000)

	def test_disabled_pricing_leaves_bom_and_price_unchanged(self):
		raw, product = self.item("Raw"), self.item("Product")
		price = self.item_price(raw, 100, self.raw_list)
		bom = self.bom(product, [{"item_code": raw, "qty": 2}])
		selling = self.item_price(product, 200, self.sales_list)
		price.price_list_rate = 300
		price.save()
		bom.reload()
		selling.reload()
		self.assertEqual(bom.total_cost, 200)
		self.assertEqual(selling.price_list_rate, 200)

	def test_mock_sms_queue_and_dispatch_in_database(self):
		self.settings.enable_sms = 1
		self.settings.sms_provider = "mock"
		self.settings.save()
		first = queue_sms("09123456789", "آزمایش", self.prefix)
		again = queue_sms("09123456789", "آزمایش", self.prefix)
		self.assertEqual(first["name"], again["name"])
		with patch.object(frappe.db, "commit"):
			result = dispatch(first["name"])
		self.assertEqual(result["status"], "Simulated")
		self.assertEqual(frappe.db.get_value("Iran Integration Request", first["name"], "attempts"), 1)

	def test_commerce_prices_are_server_calculated_and_order_is_idempotent(self):
		item = self.item("Product")
		self.item_price(item, 250, self.sales_list)
		self.settings.enable_commerce_api = 1
		self.settings.commerce_price_list = self.sales_list
		self.settings.commerce_company = self.company
		self.settings.commerce_customer = self.customer()
		self.settings.save()
		catalog = api.catalog()
		self.assertEqual(next(row for row in catalog["items"] if row.item_code == item).price, 250)
		items = [{"item_code": item, "qty": 2}]
		date = add_days(today(), 2)
		quote = api.quote(items, date)
		self.assertEqual(quote["items"][0]["rate"], 250)
		result = api.create_order(items, date, self.prefix)
		again = api.create_order(items, date, self.prefix)
		self.assertEqual(result["name"], again["name"])
		with self.assertRaises(frappe.ValidationError):
			api.create_order([{"item_code": item, "qty": 3}], date, self.prefix)
		self.assertEqual(frappe.db.get_value("Sales Order", result["name"], "docstatus"), 0)

	def test_official_invoice_snapshot_and_persian_template(self):
		item, customer = self.item("Product"), self.customer()
		self.settings.enable_official_invoice_module = 1
		self.settings.save()
		frappe.db.set_value(
			"Company", self.company, {"iran_national_id": "10380284790", "iran_postal_code": "1234567890"}
		)
		doc = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.company,
				"customer": customer,
				"currency": self.currency,
				"iran_official_invoice": 1,
				"items": [{"item_code": item, "qty": 2, "rate": 250}],
			}
		)
		doc.insert()
		self.assertEqual(doc.iran_buyer_national_id, "10380284790")
		frappe.db.set_value("Customer", customer, "iran_national_id", "changed")
		self.assertEqual(invoice_context(doc)["buyer"]["national_id"], "10380284790")
		html = frappe.db.get_value("Print Format", "Iran Official Invoice", "html")
		rendered = frappe.render_template(html, {"doc": doc})
		self.assertIn("صورتحساب رسمی فروش", rendered)
		self.assertIn(doc.name, rendered)
		self.assertIn(jalali_date(doc.posting_date), rendered)

	def test_jalali_new_year(self):
		self.assertEqual(jalali_date("2026-03-21"), "1405/01/01")

	def test_taxpayer_is_optional_and_submitted_invoice_queues_once(self):
		from iran_localization.modules.taxpayer.service import queue_invoice

		item, customer = self.item("TaxDemo"), self.customer()
		self.settings.enable_taxpayer_system = 0
		self.settings.save()
		doc = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.company,
				"customer": customer,
				"currency": self.currency,
				"items": [{"item_code": item, "qty": 2, "rate": 250}],
			}
		)
		doc.insert()
		doc.submit()
		with self.assertRaises(frappe.ValidationError):
			queue_invoice(doc.name)
		self.settings.enable_taxpayer_system = 1
		self.settings.taxpayer_provider = "mock"
		self.settings.save()
		first = queue_invoice(doc.name)
		self.assertEqual(first["name"], queue_invoice(doc.name)["name"])
		with patch.object(frappe.db, "commit"):
			self.assertEqual(dispatch(first["name"])["status"], "Simulated")
		doc.cancel()
		with self.assertRaises(frappe.ValidationError):
			queue_invoice(doc.name)

	def test_fresh_install_defaults_are_safe_and_idempotent(self):
		frappe.db.delete("Singles", {"doctype": "Iran Localization Settings"})
		frappe.clear_document_cache("Iran Localization Settings", "Iran Localization Settings")
		initialize_defaults()
		first = frappe.db.get_singles_dict("Iran Localization Settings")
		initialize_defaults()
		second = frappe.db.get_singles_dict("Iran Localization Settings")
		for key in (
			"enable_pricing_automation",
			"enable_core_validation",
			"enable_sms",
			"enable_taxpayer_system",
			"enable_commerce_api",
		):
			self.assertEqual(first[key], "0")
			self.assertEqual(second[key], "0")
		self.assertFalse(second.get("raw_material_price_list"))
		self.assertFalse(second.get("selling_price_list"))

	def test_queued_payload_is_immutable_and_provider_can_be_refreshed(self):
		from iran_localization.modules.integrations.service import refresh_provider

		self.settings.enable_sms = 1
		self.settings.sms_provider = "mock"
		self.settings.save()
		result = queue_sms("09123456789", "test", self.prefix)
		doc = frappe.get_doc("Iran Integration Request", result["name"])
		doc.payload = '{"message":"tampered"}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		self.settings.sms_sender = "new-sender"
		self.settings.save()
		with self.assertRaises(frappe.ValidationError):
			dispatch(result["name"])
		refresh_provider(result["name"])
		with patch.object(frappe.db, "commit"):
			self.assertEqual(dispatch(result["name"])["status"], "Simulated")

	def test_nonprivileged_users_cannot_access_integrations_or_commerce(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			queue_sms("09123456789", "test", self.prefix)
		with self.assertRaises(frappe.PermissionError):
			api.catalog()

	def test_calendar_boot_and_canonical_storage(self):
		from iran_localization.modules.persian_calendar.service import extend_bootinfo

		self.assertEqual(frappe.get_meta("Iran Localization Settings").get_field("enable_persian_calendar").default, "0")
		doc = frappe.get_doc({"doctype": "ToDo", "description": self.prefix + " calendar", "date": "2026-10-13"}).insert()
		for enabled in (1, 0):
			frappe.db.set_single_value("Iran Localization Settings", "enable_persian_calendar", enabled)
			frappe.clear_document_cache("Iran Localization Settings", "Iran Localization Settings")
			boot = frappe._dict()
			extend_bootinfo(boot)
			self.assertEqual(boot.iran_localization["enable_persian_calendar"], bool(enabled))
			doc.reload()
			self.assertEqual(str(doc.date), "2026-10-13")
			self.assertEqual(str(frappe.db.get_value("ToDo", doc.name, "date")), "2026-10-13")
		self.assertEqual(frappe.render_template('{{ jalali_date("2026-10-13") }}', {}), "1405/07/21")
