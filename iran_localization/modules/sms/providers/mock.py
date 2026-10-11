class MockSMSProvider:
	key = "mock"
	label = "Test provider (no SMS delivery)"
	simulated = True

	def send(self, payload, idempotency_key, settings):
		return {"reference": "mock:" + idempotency_key}
