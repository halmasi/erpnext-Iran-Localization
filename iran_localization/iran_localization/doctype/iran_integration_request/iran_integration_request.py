import frappe
from frappe import _
from frappe.model.document import Document


class IranIntegrationRequest(Document):
	def validate(self):
		previous = self.get_doc_before_save()
		if not previous:
			return
		for key in (
			"integration",
			"provider",
			"payload",
			"idempotency_key",
			"reference_doctype",
			"reference_name",
			"provider_config_fingerprint",
		):
			if self.flags.iran_integration_reconfigure and key in (
				"provider",
				"payload",
				"provider_config_fingerprint",
			):
				continue
			if previous.get(key) != self.get(key):
				frappe.throw(_("Queued request identity and payload cannot be edited."))
		if not self.flags.iran_integration_update:
			frappe.throw(_("Use the integration actions to update this request."))
