import requests

from iran_localization.modules.integrations.service import ProviderRejected


class KavenegarProvider:
	key = "kavenegar"
	label = "Kavenegar"
	simulated = False

	def send(self, payload, idempotency_key, settings):
		secret = settings.get_password("sms_api_key", raise_exception=False)
		if not secret or not settings.sms_sender:
			raise ProviderRejected("Missing credentials")
		response = requests.post(
			f"https://api.kavenegar.com/v1/{secret}/sms/send.json",
			data={
				"receptor": payload["recipient"],
				"message": payload["message"],
				"sender": settings.sms_sender,
			},
			timeout=(5, 30),
			allow_redirects=False,
		)
		response.raise_for_status()
		result = response.json()
		if result.get("return", {}).get("status") != 200:
			raise ProviderRejected("Rejected")
		return {"reference": str(result["entries"][0]["messageid"])}
