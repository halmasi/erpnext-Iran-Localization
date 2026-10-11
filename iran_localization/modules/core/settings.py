"""Site settings; schema belongs to the app, values belong to the site."""

import frappe
from frappe.utils import cint

SETTINGS_DOCTYPE = "Iran Localization Settings"


def get_settings():
	return frappe.get_single(SETTINGS_DOCTYPE)


def is_enabled(fieldname):
	return bool(cint(get_settings().get(fieldname)))


def initialize_defaults():
	"""Populate only absent values, preserving explicit zero and empty selections."""
	existing = frappe.db.get_singles_dict(SETTINGS_DOCTYPE)
	legacy = {
		"enable_core_validation": "enable_iran_validations",
		"enable_official_invoice_module": "enable_official_invoice",
	}
	values = {}
	for field in frappe.get_meta(SETTINGS_DOCTYPE).fields:
		if field.fieldname in existing or field.default is None:
			continue
		source = legacy.get(field.fieldname)
		values[field.fieldname] = existing.get(source, field.default)
	if values:
		frappe.db.set_single_value(SETTINGS_DOCTYPE, values)
	frappe.clear_document_cache(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE)
