"""Apply the Persian language switch without changing ERPNext core."""

import frappe
from frappe.utils import cint


def apply_language_settings(settings):
	old = settings.get_doc_before_save()
	enabled = bool(cint(settings.enable_persian_language))
	was_enabled = bool(cint(old.get("enable_persian_language"))) if old else False
	if enabled == was_enabled:
		return

	if enabled:
		users = frappe.get_all("User", filters={"name": ["!=", "Guest"]}, fields=["name", "language"])
		previous = {
			"system": frappe.db.get_single_value("System Settings", "language"),
			"users": {user.name: user.language for user in users},
		}
		settings.db_set("previous_language_settings", frappe.as_json(previous), update_modified=False)
		language = frappe.get_doc("Language", "fa")
		if not language.enabled:
			language.enabled = 1
			language.save()
		set_system_language("fa")
		for user in users:
			frappe.db.set_value("User", user.name, "language", "fa", update_modified=False)
	else:
		previous = frappe.parse_json(old.get("previous_language_settings") or "{}")
		if frappe.db.get_single_value("System Settings", "language") == "fa":
			set_system_language(previous.get("system") or "en")
		for user, language in previous.get("users", {}).items():
			# Preserve preferences changed explicitly after activation.
			if frappe.db.get_value("User", user, "language") == "fa":
				frappe.db.set_value("User", user, "language", language, update_modified=False)
		settings.db_set("previous_language_settings", None, update_modified=False)

	# Other workers must rebuild both translations and user boot data after commit.
	frappe.db.after_commit.add(clear_language_cache)


def set_system_language(language):
	system_settings = frappe.get_single("System Settings")
	system_settings.language = language
	system_settings.save()


def clear_language_cache():
	from frappe.translate import clear_cache

	clear_cache()
	frappe.clear_cache()
