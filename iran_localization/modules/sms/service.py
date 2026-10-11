import re

import frappe
from frappe import _

from iran_localization.modules.core.validation import normalize_digits
from iran_localization.modules.integrations.service import create_request


def normalize_mobile(value):
	value = normalize_digits(value).replace(" ", "").replace("-", "")
	if value.startswith("+98"):
		value = "0" + value[3:]
	elif value.startswith("0098"):
		value = "0" + value[4:]
	if not re.fullmatch(r"09[0-9]{9}", value):
		frappe.throw(_("Enter a valid Iranian mobile number."))
	return value


@frappe.whitelist(methods=["POST"])
def queue_sms(recipient, message, request_id):
	frappe.only_for("System Manager")
	if not isinstance(message, str) or not message.strip() or len(message) > 2000:
		frappe.throw(_("SMS message must contain 1–2000 characters."))
	if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", request_id):
		frappe.throw(_("Provide a unique request ID with 8–80 letters, digits, underscores or hyphens."))
	request = create_request(
		"sms", {"recipient": normalize_mobile(recipient), "message": message}, "sms:" + request_id
	)
	return {"name": request.name, "status": request.status}
