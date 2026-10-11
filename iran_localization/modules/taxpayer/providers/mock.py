class MockTaxpayerProvider:
	key = "mock"
	label = "Test provider (no tax submission)"
	simulated = True

	def send(self, payload, idempotency_key, settings):
		return {"reference": "mock:" + idempotency_key}
