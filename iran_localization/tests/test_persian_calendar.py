"""Calendar utilities and settings contract; no accounting date overrides."""

import unittest
from datetime import date, datetime
from unittest.mock import patch

import frappe

from iran_localization.modules.persian_calendar import service
from iran_localization.modules.persian_calendar.utils import normalize_digits, to_gregorian, to_jalali


class TestPersianCalendar(unittest.TestCase):
	def test_required_conversion(self):
		self.assertEqual(to_jalali("2026-10-13"), "1405/07/21")
		self.assertEqual(to_gregorian("1405/07/21"), "2026-10-13")

	def test_nowruz(self):
		self.assertEqual(to_jalali("2026-03-20"), "1404/12/29")
		self.assertEqual(to_jalali("2026-03-21"), "1405/01/01")

	def test_esfand_leap(self):
		self.assertEqual(to_gregorian("1403/12/30"), "2025-03-20")
		self.assertEqual(to_jalali("2025-03-21"), "1404/01/01")
		self.assertEqual(to_gregorian("1404/12/29"), "2026-03-20")

	def test_invalid_jalali(self):
		for value in (
			"1404/12/30",
			"1405/13/01",
			"1405/00/01",
			"1405/01/32",
			"1405/01/00",
			"1405/07/31",
			"1405/02/1junk",
			"2026-10-13",
		):
			with self.subTest(value=value), self.assertRaises(ValueError):
				to_gregorian(value)

	def test_gregorian_leap(self):
		self.assertEqual(to_gregorian(to_jalali("2024-02-29")), "2024-02-29")
		for value in ("2025-02-29", "2026-13-01", "2026-01-00", "2026-04-31", "1405/07/21"):
			with self.subTest(value=value), self.assertRaises(ValueError):
				to_jalali(value)

	def test_digits(self):
		self.assertEqual(to_gregorian("۱۴۰۵/۰۷/۲۱"), "2026-10-13")  # noqa: RUF001
		self.assertEqual(to_gregorian("١٤٠٥/٠٧/٢١"), "2026-10-13")  # noqa: RUF001
		self.assertEqual(normalize_digits(" ۱۲٣ "), "123")

	def test_empty(self):
		for value in (None, ""):
			self.assertEqual(to_jalali(value), "")
			self.assertEqual(to_gregorian(value), "")

	def test_date_objects(self):
		self.assertEqual(to_jalali(date(2026, 10, 13)), "1405/07/21")
		self.assertEqual(to_jalali(datetime(2026, 10, 13, 14, 30)), "1405/07/21")

	def test_month_boundaries(self):
		for value in ("1405/06/31", "1405/07/01", "1405/11/30", "1405/12/01", "1403/12/30"):
			self.assertEqual(to_jalali(to_gregorian(value)), value)

	def test_setting_disabled(self):
		boot = frappe._dict()
		with patch.object(service, "is_enabled", return_value=False) as enabled:
			service.extend_bootinfo(boot)
			enabled.assert_called_once_with("enable_persian_calendar")
		self.assertIs(boot.iran_localization["enable_persian_calendar"], False)

	def test_setting_enabled(self):
		boot = frappe._dict()
		with patch.object(service, "is_enabled", return_value=True):
			service.extend_bootinfo(boot)
		self.assertIs(boot.iran_localization["enable_persian_calendar"], True)
