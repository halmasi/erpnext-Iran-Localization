"""Optional Iranian account details using ERPNext's existing Bank masters."""

import re

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from iran_localization.modules.core.settings import get_settings

BANKS = (
	"بانک ملی ایران", "بانک سپه", "بانک ملت", "بانک تجارت", "بانک صادرات ایران",
	"بانک کشاورزی", "بانک مسکن", "بانک رفاه کارگران", "بانک صنعت و معدن",
	"بانک توسعه صادرات ایران", "بانک توسعه تعاون", "پست بانک ایران",
	"بانک اقتصاد نوین", "بانک پارسیان", "بانک پاسارگاد", "بانک سامان",
	"بانک سرمایه", "بانک سینا", "بانک شهر", "بانک دی", "بانک ایران زمین",
	"بانک خاورمیانه", "بانک کارآفرین", "بانک گردشگری",
	"بانک قرض‌الحسنه رسالت", "بانک قرض‌الحسنه مهر ایران",
)


def setup():
	create_custom_fields({
		"Bank Account": [{"fieldname": "iran_sheba", "label": "شماره شبا",
			"fieldtype": "Data", "insert_after": "iban", "hidden": 1,
			"description": "۲۴ رقم، با یا بدون پیشوند IR؛ ارقام فارسی نیز پذیرفته می‌شوند."},
			{"fieldname": "iran_card_number", "label": "شماره کارت",
			"fieldtype": "Data", "insert_after": "bank_account_no", "hidden": 1}],
		"Bank": [{"fieldname": "iran_bank", "label": "بانک ایرانی",
			"fieldtype": "Check", "insert_after": "bank_name", "default": "0"}],
	})
	apply_settings(get_settings())


def apply_settings(settings):
	if settings.get("enable_iran_bank_list"):
		for name in BANKS:
			if not frappe.db.exists("Bank", name):
				frappe.get_doc({"doctype": "Bank", "bank_name": name, "iran_bank": 1}).insert(ignore_permissions=True)
			else:
				frappe.db.set_value("Bank", name, "iran_bank", 1, update_modified=False)


@frappe.whitelist()
def options():
	frappe.has_permission("Bank Account", "read", throw=True)
	s = get_settings()
	return {key: bool(s.get(key)) for key in
		("enable_iran_sheba", "enable_iran_card_number", "enable_iran_bank_list")}


def validate_account(doc, method=None):
	s = get_settings()
	if s.get("enable_iran_sheba") and doc.get("iran_sheba"):
		value = normalize(doc.iran_sheba)
		if not value.startswith("IR"):
			value = "IR" + value
		if not re.fullmatch(r"IR[0-9]{24}", value):
			frappe.throw("شماره شبا باید شامل IR و ۲۴ رقم باشد.")
		if int(value[4:] + "1827" + value[2:4]) % 97 != 1:
			frappe.throw("شماره شبا معتبر نیست.")
		doc.iran_sheba = value[2:]
	if s.get("enable_iran_card_number") and doc.get("iran_card_number"):
		value = normalize(doc.iran_card_number)
		if not re.fullmatch(r"[0-9]{16}", value):
			frappe.throw("شماره کارت باید ۱۶ رقم باشد.")
		doc.iran_card_number = value


def normalize(value):
	return re.sub(r"[\s-]", "", value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))).upper()
