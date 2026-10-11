import re

import frappe
from frappe import _

from iran_localization.modules.core.settings import get_settings

DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value):
	return str(value).strip().translate(DIGIT_TRANSLATION) if value is not None else ""


def valid_personal_id(value):
	value = normalize_digits(value)
	if not re.fullmatch(r"[0-9]{10}", value) or len(set(value)) == 1:
		return False
	remainder = sum(int(digit) * (10 - index) for index, digit in enumerate(value[:9])) % 11
	return int(value[-1]) == (remainder if remainder < 2 else 11 - remainder)


def valid_legal_id(value):
	value = normalize_digits(value)
	if not re.fullmatch(r"[0-9]{11}", value) or len(set(value)) == 1 or int(value[3:9]) == 0:
		return False
	offset = int(value[9]) + 2
	weights = (29, 27, 23, 19, 17)
	remainder = sum((int(digit) + offset) * weights[index % 5] for index, digit in enumerate(value[:10])) % 11
	return int(value[-1]) == (0 if remainder == 10 else remainder)


def iran_validations_enabled():
	return bool(get_settings().enable_core_validation)


def validate_iran_fields(doc, method=None):
	settings = get_settings()
	if not settings.enable_core_validation:
		return
	for key in ("iran_postal_code", "iran_national_id", "iran_economic_code", "iran_registration_number"):
		if doc.get(key):
			doc.set(key, normalize_digits(doc.get(key)))
	postal_code = doc.get("iran_postal_code")
	national_id = doc.get("iran_national_id")
	if postal_code and not re.fullmatch(r"[0-9]{10}", postal_code):
		frappe.throw(_("کد پستی باید دقیقاً ۱۰ رقم باشد."))
	if national_id and not re.fullmatch(r"[0-9]{10,11}", national_id):
		frappe.throw(_("شناسه ملی باید فقط شامل ارقام و با طول معتبر باشد."))
	if settings.enable_strict_national_id and national_id:
		validator = valid_personal_id if len(national_id) == 10 else valid_legal_id
		if not validator(national_id):
			frappe.throw(_("رقم کنترل شناسه ملی معتبر نیست."))
