"""Bridge to a replaceable trusted gateway implementing the documented v1 contract."""

from urllib.parse import urlsplit

import requests

from iran_localization.modules.integrations.service import ProviderRejected


class HTTPGatewayProvider:
	key = "http_gateway"
	label = "Taxpayer gateway (adapter contract v1)"
	simulated = False

	def send(self, payload, idempotency_key, settings):
		endpoint = settings.taxpayer_endpoint or ""
		parsed = urlsplit(endpoint)
		if (
			parsed.scheme != "https"
			or not parsed.hostname
			or parsed.username
			or parsed.password
			or parsed.fragment
		):
			raise ProviderRejected("HTTPS endpoint required")
		secret = settings.get_password("taxpayer_api_key", raise_exception=False)
		if not secret or not payload.get("memory_id"):
			raise ProviderRejected("Missing credentials or memory ID")
		response = requests.post(
			endpoint,
			json={"contract_version": 1, "idempotency_key": idempotency_key, "invoice": payload},
			headers={"Authorization": "Bearer " + secret, "Idempotency-Key": idempotency_key},
			timeout=(5, 30),
			allow_redirects=False,
		)
		response.raise_for_status()
		result = response.json()
		if result.get("accepted") is False:
			raise ProviderRejected("Rejected")
		if (
			result.get("accepted") is not True
			or not isinstance(result.get("reference"), str)
			or not result["reference"]
		):
			raise ValueError("Ambiguous gateway response")
		return {"reference": result["reference"]}
