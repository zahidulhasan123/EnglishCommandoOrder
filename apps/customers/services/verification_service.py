import os

import requests


class VerificationService:
	"""Client for the external activation-code /generate endpoint (see documents/someapi.md)."""

	@staticmethod
	def _headers() -> dict:
		return {
			"X-API-KEY": os.getenv("VERIFICATION_GENERATE_KEY", ""),
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

	@staticmethod
	def generate_code(phone_number: str) -> tuple[bool, str]:
		base_url = os.getenv("VERIFICATION_API_BASE_URL", "").rstrip("/")
		api_key = os.getenv("VERIFICATION_GENERATE_KEY", "")
		if not base_url or not api_key:
			return False, "Verification API is not configured."

		try:
			response = requests.post(
				f"{base_url}/generate",
				json={"phone_number": phone_number},
				headers=VerificationService._headers(),
				timeout=15,
			)
		except requests.RequestException as exc:
			return False, f"Request failed: {exc}"

		try:
			data = response.json()
		except ValueError:
			data = {}

		if response.status_code == 201 and data.get("success"):
			return True, f"Activation code generated for {phone_number}."

		message = data.get("message") or f"Failed with status {response.status_code}"
		return False, message
