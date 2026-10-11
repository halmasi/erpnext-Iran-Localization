"""Convert the existing custom settings schema without touching tabSingles."""

import frappe


def execute():
	name = "Iran Localization Settings"
	if frappe.db.exists("DocType", name):
		frappe.db.set_value("DocType", name, "custom", 0, update_modified=False)
		frappe.clear_cache(doctype=name)
