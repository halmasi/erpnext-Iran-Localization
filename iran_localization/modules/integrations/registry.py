"""Providers are installed code registered through hooks, never user supplied paths."""

import frappe
from frappe import _


def providers(kind):
	if kind not in ("sms", "taxpayer"):
		frappe.throw(_("Unknown integration type."))
	result = {}
	for path in frappe.get_hooks(f"iran_{kind}_providers"):
		cls = frappe.get_attr(path)
		key = cls.key
		if key in result:
			frappe.throw(_("Duplicate provider key: {0}").format(key))
		result[key] = cls
	return result


def get_provider(kind, key):
	cls = providers(kind).get(key)
	if cls is None:
		frappe.throw(_("Provider {0} is not installed for {1}.").format(key, kind))
	return cls()


@frappe.whitelist()
def list_providers():
	frappe.only_for("System Manager")
	return {
		kind: [
			{"key": key, "label": cls.label, "simulated": cls.simulated}
			for key, cls in providers(kind).items()
		]
		for kind in ("sms", "taxpayer")
	}
