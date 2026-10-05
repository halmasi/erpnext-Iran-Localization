import re
import frappe
from frappe import _


def iran_validations_enabled():
    try:
        return frappe.db.get_single_value(
            "Iran Localization Settings", "enable_iran_validations"
        )
    except Exception:
        return True


def validate_iran_fields(doc, method=None):
    if not iran_validations_enabled():
        return

    postal_code = getattr(doc, "iran_postal_code", None)
    national_id = getattr(doc, "iran_national_id", None)

    if postal_code and not re.fullmatch(r"\d{10}", postal_code):
        frappe.throw(_("کد پستی باید دقیقاً ۱۰ رقم باشد."))

    if national_id and not re.fullmatch(r"\d{10,11}", national_id):
        frappe.throw(_("شناسه ملی باید فقط شامل ارقام و با طول معتبر باشد."))
