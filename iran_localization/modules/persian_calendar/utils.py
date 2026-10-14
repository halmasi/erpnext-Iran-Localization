"""Shared print/calendar conversion helpers using the existing jdatetime dependency."""

import re
from datetime import date, datetime

import jdatetime

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value):
	return "" if value is None else str(value).translate(_DIGITS).strip()


def _parts(value, separator):
	value = normalize_digits(value)
	if not re.fullmatch(rf"\d{{4}}{separator}\d{{1,2}}{separator}\d{{1,2}}", value):
		raise ValueError("Expected a year/month/day date")
	return tuple(map(int, value.split(separator)))


def to_jalali(value):
	"""Gregorian ISO date (or date object) to YYYY/MM/DD; empty stays empty."""
	if value is None or value == "":
		return ""
	if isinstance(value, datetime):
		value = value.date()
	if not isinstance(value, date):
		value = date(*_parts(value, "-"))
	converted = jdatetime.date.fromgregorian(date=value)
	return f"{converted.year:04d}/{converted.month:02d}/{converted.day:02d}"


def to_gregorian(value):
	"""Strict Jalali YYYY/MM/DD to Gregorian ISO; reject invalid dates."""
	if value is None or value == "":
		return ""
	return jdatetime.date(*_parts(value, "/")).togregorian().isoformat()


# Public Jinja helper; also used by official_invoice for backwards compatibility.
def jalali_date(value):
	return to_jalali(value)
