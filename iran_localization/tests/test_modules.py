"""Fast module tests. Run through bench run-tests or the documented standalone runner."""

import json
import unittest
from unittest.mock import MagicMock, patch

import frappe

from iran_localization.modules.commerce import api
from iran_localization.modules.core import settings, validation
from iran_localization.modules.integrations import service as integrations
from iran_localization.modules.pricing import service as pricing
from iran_localization.modules.sms.service import normalize_mobile


class TestValidation(unittest.TestCase):
	def test_personal_checksum_and_digit_normalization(self):
		self.assertTrue(validation.valid_personal_id("۰۴۹۹۳۷۰۸۹۹"))
		self.assertFalse(validation.valid_personal_id("0499370898"))
		self.assertFalse(validation.valid_personal_id("1111111111"))
		self.assertFalse(validation.valid_personal_id("abcdefghij"))

	def test_legal_checksum(self):
		self.assertTrue(validation.valid_legal_id("10380284790"))
		self.assertFalse(validation.valid_legal_id("10380284791"))
		self.assertFalse(validation.valid_legal_id("00000000000"))

	def test_optional_and_empty_fields(self):
		doc = frappe.get_doc({"doctype": "Customer", "iran_postal_code": "wrong"})
		with patch.object(validation, "get_settings", return_value=frappe._dict(enable_core_validation=0)):
			validation.validate_iran_fields(doc)
		with patch.object(validation, "get_settings", return_value=frappe._dict(enable_core_validation=1)):
			with self.assertRaises(frappe.ValidationError):
				validation.validate_iran_fields(doc)
			doc.iran_postal_code = ""
			validation.validate_iran_fields(doc)

	def test_mobile_normalization(self):
		self.assertEqual(normalize_mobile("+98 912-345-6789"), "09123456789")
		self.assertEqual(normalize_mobile("۰۹۱۲۳۴۵۶۷۸۹"), "09123456789")
		with self.assertRaises(frappe.ValidationError):
			normalize_mobile("123")


class TestSettings(unittest.TestCase):
	def test_defaults_preserve_zero_empty_and_site_price_lists(self):
		fields = [
			frappe._dict(fieldname=key, default=value)
			for key, value in (
				("enable_core_validation", "1"),
				("raw_material_price_list", None),
				("selling_price_list", None),
				("enable_sms", "0"),
			)
		]
		existing = {
			"enable_core_validation": "0",
			"raw_material_price_list": "site-list",
			"selling_price_list": "",
		}
		with (
			patch.object(frappe.db, "get_singles_dict", return_value=existing),
			patch.object(frappe, "get_meta", return_value=frappe._dict(fields=fields)),
			patch.object(frappe.db, "set_single_value") as write,
		):
			settings.initialize_defaults()
			write.assert_called_once_with(settings.SETTINGS_DOCTYPE, {"enable_sms": "0"})

	def test_legacy_switch_is_migrated_only_if_new_field_is_absent(self):
		fields = [frappe._dict(fieldname="enable_core_validation", default="0")]
		with (
			patch.object(frappe.db, "get_singles_dict", return_value={"enable_iran_validations": "1"}),
			patch.object(frappe, "get_meta", return_value=frappe._dict(fields=fields)),
			patch.object(frappe.db, "set_single_value") as write,
		):
			settings.initialize_defaults()
			write.assert_called_once_with(settings.SETTINGS_DOCTYPE, {"enable_core_validation": "1"})


class TestPricing(unittest.TestCase):
	def setUp(self):
		self.settings = frappe._dict(
			enable_pricing_automation=1,
			raw_material_price_list="Raw",
			selling_price_list="Sales",
			manufacturing_overhead_percent="10",
			profit_markup_percent="20",
		)
		frappe.flags.iran_pricing_running = False

	def tearDown(self):
		frappe.flags.iran_pricing_running = False

	def test_disabled_and_unrelated_prices_do_not_touch_boms(self):
		with (
			patch.object(pricing, "get_settings", return_value=self.settings),
			patch.object(pricing, "_update_dependent_boms_and_prices") as update,
		):
			pricing.update_product_prices_from_raw_material(frappe._dict(price_list="Other"))
			self.settings.enable_pricing_automation = 0
			pricing.update_product_prices_from_raw_material(frappe._dict(price_list="Raw"))
			update.assert_not_called()

	def test_missing_settings_do_not_touch_boms(self):
		self.settings.selling_price_list = ""
		with (
			patch.object(pricing, "get_settings", return_value=self.settings),
			patch.object(pricing, "_update_dependent_boms_and_prices") as update,
		):
			pricing.update_product_prices_from_raw_material(frappe._dict(price_list="Raw"))
			update.assert_not_called()

	def test_guard_clears_on_error(self):
		with (
			patch.object(pricing, "get_settings", return_value=self.settings),
			patch.object(pricing, "_update_dependent_boms_and_prices", side_effect=ValueError),
		):
			with self.assertRaises(ValueError):
				pricing.update_product_prices_from_raw_material(frappe._dict(price_list="Raw", item_code="R"))
		self.assertFalse(frappe.flags.iran_pricing_running)

	def test_diamond_graph_child_costs_precede_shared_parent(self):
		a = frappe._dict(name="A", item="A-item", is_default=1)
		b = frappe._dict(name="B", item="B-item", is_default=1)
		final = frappe._dict(name="F", item="F-item", is_default=1)
		children = {"R": [a, b], "A-item": [final], "B-item": [final]}
		with patch.object(pricing, "_dependent_boms", side_effect=lambda item: children.get(item, [])):
			nodes, order = pricing._collect_graph("R")
		self.assertEqual(set(nodes), {"A", "B", "F"})
		self.assertLess(order.index("A"), order.index("F"))
		self.assertLess(order.index("B"), order.index("F"))
		self.assertEqual(order.count("F"), 1)

	def test_cycle_is_rejected_before_cost_updates(self):
		a = frappe._dict(name="A", item="A-item", is_default=1)
		b = frappe._dict(name="B", item="B-item", is_default=1)
		children = {"R": [a], "A-item": [b], "B-item": [a]}
		with (
			patch.object(pricing, "_dependent_boms", side_effect=lambda item: children.get(item, [])),
			patch.object(frappe, "get_doc") as get_doc,
		):
			with self.assertRaises(frappe.ValidationError):
				pricing._update_dependent_boms_and_prices("R", self.settings, set())
			get_doc.assert_not_called()

	def test_quantity_and_markup_are_applied_per_output_unit(self):
		row = frappe._dict(name="A", item="Product", is_default=1)
		bom = MagicMock(item="Product", quantity=4, total_cost=1000, currency="IRR", uom="Nos")
		with (
			patch.object(pricing, "_collect_graph", return_value=({"A": row}, ["A"])),
			patch.object(frappe, "get_doc", return_value=bom),
			patch.object(frappe.db, "get_value", return_value="IRR"),
			patch.object(pricing, "_update_selling_price") as update,
		):
			pricing._update_dependent_boms_and_prices("R", self.settings, set())
			update.assert_called_once_with("Product", 250, self.settings, uom="Nos")
			bom.update_cost.assert_called_once_with(update_parent=False)

	def test_existing_price_updated_without_overwriting_customer_price(self):
		generic = frappe._dict(name="Generic", valid_from="2026-01-01", packing_unit=0)
		customer = frappe._dict(name="Special", customer="Customer", packing_unit=0)
		price = MagicMock()
		price.precision.return_value = 2
		with (
			patch.object(frappe, "get_all", return_value=[customer, generic]),
			patch.object(frappe, "get_doc", return_value=price) as get_doc,
		):
			pricing._update_selling_price("Product", 100, self.settings, "Nos")
			get_doc.assert_called_once_with("Item Price", "Generic")
			self.assertEqual(price.price_list_rate, 132)
			price.save.assert_called_once_with(ignore_permissions=True)

	def test_missing_price_inserted(self):
		price = MagicMock()
		price.precision.return_value = 2
		with (
			patch.object(frappe, "get_all", return_value=[]),
			patch.object(frappe, "get_doc", return_value=price),
		):
			pricing._update_selling_price("Product", 100, self.settings, "Nos")
			self.assertEqual(price.price_list_rate, 132)
			price.insert.assert_called_once_with(ignore_permissions=True)


class TestIntegrations(unittest.TestCase):
	def setUp(self):
		self.settings = frappe._dict(enable_sms=1, sms_provider="mock", enable_taxpayer_system=0)

	def test_disabled_module_cannot_queue(self):
		with patch.object(integrations, "get_settings", return_value=self.settings):
			with self.assertRaises(frappe.ValidationError):
				integrations.create_request("taxpayer", {}, "tax:key")

	def test_sms_request_id_cannot_be_reused_for_different_payload(self):
		request = frappe._dict(provider="mock", integration="SMS", payload='{"message": "old"}')
		with (
			patch.object(integrations, "get_settings", return_value=self.settings),
			patch.object(integrations, "get_provider"),
			patch.object(frappe.db, "get_value", return_value="existing"),
			patch.object(frappe, "get_doc", return_value=request),
		):
			with self.assertRaises(frappe.ValidationError):
				integrations.create_request("sms", {"message": "new"}, "sms:key")

	def test_mock_dispatch_is_simulated_and_repeat_does_not_send(self):
		request = MagicMock()
		request.name = "Request"
		request.status = "Pending"
		request.integration = "SMS"
		request.provider = "mock"
		request.reference_doctype = None
		request.payload = '{"message": "test"}'
		request.attempts = 0
		request.provider_config_fingerprint = integrations.provider_fingerprint("sms", "mock", self.settings)
		provider = MagicMock(simulated=True)
		provider.send.return_value = {"reference": "mock:key"}
		with (
			patch.object(integrations, "get_settings", return_value=self.settings),
			patch.object(frappe, "get_doc", return_value=request),
			patch.object(frappe.db, "commit"),
			patch.object(integrations, "get_provider", return_value=provider),
		):
			self.assertEqual(integrations.dispatch("Request")["status"], "Simulated")
			integrations.dispatch("Request")
			provider.send.assert_called_once()

	def test_timeout_is_unknown_and_does_not_leak_secrets(self):
		request = MagicMock(
			status="Pending",
			integration="SMS",
			provider="mock",
			reference_doctype=None,
			payload="{}",
			attempts=0,
		)
		provider = MagicMock(simulated=False)
		request.provider_config_fingerprint = integrations.provider_fingerprint("sms", "mock", self.settings)
		provider.send.side_effect = TimeoutError("secret-url")
		with (
			patch.object(integrations, "get_settings", return_value=self.settings),
			patch.object(frappe, "get_doc", return_value=request),
			patch.object(frappe.db, "commit"),
			patch.object(integrations, "get_provider", return_value=provider),
		):
			integrations.dispatch("Request")
			self.assertEqual(request.status, "Unknown")
			self.assertNotIn("secret", request.error)
			with self.assertRaises(frappe.ValidationError):
				integrations.retry_request("Request")

	def test_changed_provider_account_cannot_send_old_request(self):
		request = MagicMock(
			status="Pending",
			integration="SMS",
			provider="mock",
			reference_doctype=None,
			provider_config_fingerprint="old-account",
		)
		with (
			patch.object(integrations, "get_settings", return_value=self.settings),
			patch.object(frappe, "get_doc", return_value=request),
			patch.object(integrations, "get_provider") as provider,
		):
			with self.assertRaises(frappe.ValidationError):
				integrations.dispatch("Request")
			provider.assert_not_called()


class TestProviders(unittest.TestCase):
	def test_kavenegar_contract(self):
		from iran_localization.modules.sms.providers.kavenegar import KavenegarProvider

		settings = MagicMock(sms_sender="1000")
		settings.get_password.return_value = "test-key"
		response = MagicMock()
		response.json.return_value = {"return": {"status": 200}, "entries": [{"messageid": 123}]}
		with patch(
			"iran_localization.modules.sms.providers.kavenegar.requests.post", return_value=response
		) as post:
			result = KavenegarProvider().send(
				{"recipient": "09123456789", "message": "test"}, "test-id", settings
			)
			self.assertEqual(result["reference"], "123")
			self.assertEqual(post.call_args.kwargs["data"]["receptor"], "09123456789")
			self.assertFalse(post.call_args.kwargs["allow_redirects"])

	def test_gateway_acceptance_and_rejection(self):
		from iran_localization.modules.taxpayer.providers.http_gateway import HTTPGatewayProvider

		settings = MagicMock(taxpayer_endpoint="https://gateway.example/invoices")
		settings.get_password.return_value = "test-token"
		response = MagicMock()
		response.json.return_value = {"accepted": True, "reference": "ref-123"}
		with patch(
			"iran_localization.modules.taxpayer.providers.http_gateway.requests.post", return_value=response
		) as post:
			result = HTTPGatewayProvider().send({"memory_id": "TEST"}, "tax:123", settings)
			self.assertEqual(result["reference"], "ref-123")
			self.assertEqual(post.call_args.kwargs["headers"]["Idempotency-Key"], "tax:123")
			response.json.return_value = {"accepted": False}
			with self.assertRaises(integrations.ProviderRejected):
				HTTPGatewayProvider().send({"memory_id": "TEST"}, "tax:123", settings)

	def test_gateway_ambiguous_response_does_not_claim_delivery(self):
		from iran_localization.modules.taxpayer.providers.http_gateway import HTTPGatewayProvider

		settings = MagicMock(taxpayer_endpoint="https://gateway.example/invoices")
		settings.get_password.return_value = "test-token"
		response = MagicMock()
		response.json.return_value = {"reference": "maybe"}
		with patch(
			"iran_localization.modules.taxpayer.providers.http_gateway.requests.post", return_value=response
		):
			with self.assertRaises(ValueError):
				HTTPGatewayProvider().send({"memory_id": "TEST"}, "tax:123", settings)


class TestCommerce(unittest.TestCase):
	def test_disabled_api(self):
		with patch.object(api, "get_settings", return_value=frappe._dict(enable_commerce_api=0)):
			with self.assertRaises(frappe.ValidationError):
				api.catalog()

	def test_client_cannot_choose_prices(self):
		doc = MagicMock()
		with patch.object(frappe, "new_doc", return_value=doc):
			with self.assertRaises(frappe.ValidationError):
				api._order(frappe._dict(), [{"item_code": "Item", "qty": 1, "rate": 1}], "2099-01-01")

	def test_empty_cart(self):
		with self.assertRaises(frappe.ValidationError):
			api._order(frappe._dict(), [], "2099-01-01")
