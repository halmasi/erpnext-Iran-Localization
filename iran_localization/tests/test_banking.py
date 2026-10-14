import unittest
from unittest.mock import patch

import frappe

from iran_localization.modules import banking


class TestBanking(unittest.TestCase):
	def test_normalization_and_valid_sheba(self):
		doc = frappe._dict(iban="DE-original", iran_sheba="ir۳۸ ۰۱۷۰ ۰۰۰۰ ۰۰۱۰ ۰۰۰۰ ۰۰۰۰ ۰۱", iran_card_number="۶۰۳۷-۹۹۱۲-۳۴۵۶-۷۸۹۰")
		with patch.object(banking, "get_settings", return_value=frappe._dict(enable_iran_sheba=1, enable_iran_card_number=1)):
			banking.validate_account(doc)
		self.assertEqual(doc.iran_sheba, "380170000000100000000001")
		self.assertEqual(doc.iban, "DE-original")
		self.assertEqual(doc.iran_card_number, "6037991234567890")

	def test_disabled_keeps_existing_foreign_account(self):
		doc = frappe._dict(iban="DE-test", iran_card_number="legacy")
		with patch.object(banking, "get_settings", return_value=frappe._dict()):
			banking.validate_account(doc)
		self.assertEqual(doc.iban, "DE-test")

	def test_invalid_checksum_is_rejected(self):
		with patch.object(banking, "get_settings", return_value=frappe._dict(enable_iran_sheba=1)):
			with self.assertRaises(frappe.ValidationError):
				banking.validate_account(frappe._dict(iran_sheba="IR000170000000100000000001"))

	def test_digits_without_country_prefix(self):
		doc = frappe._dict(iran_sheba="380170000000100000000001")
		with patch.object(banking, "get_settings", return_value=frappe._dict(enable_iran_sheba=1)):
			banking.validate_account(doc)
		self.assertEqual(doc.iran_sheba, "380170000000100000000001")
