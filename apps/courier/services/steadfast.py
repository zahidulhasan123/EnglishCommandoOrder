import os

import requests

from apps.courier.services.base import BaseCourierClient


class SteadfastClient(BaseCourierClient):
    def __init__(self):
        self.base_url = os.getenv("STEADFAST_API_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("STEADFAST_API_KEY", "")
        self.secret_key = os.getenv("STEADFAST_SECRET_KEY", "")

    def _headers(self) -> dict:
        return {
            "Api-Key": self.api_key,
            "Secret-Key": self.secret_key,
            "Content-Type": "application/json",
        }

    def create_shipment(self, order):
        if not self.base_url or not self.api_key or not self.secret_key:
            raise ValueError("Steadfast credentials are not configured.")

        payload = {
            "invoice": order.order_number,
            "recipient_name": order.customer.name,
            "recipient_phone": order.customer.phone,
            "recipient_address": order.customer.address,
            "cod_amount": str(order.total_amount),
            "note": order.customer_note,
        }
        response = requests.post(
            f"{self.base_url}/create_order",
            json=payload,
            headers=self._headers(),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_status(self, shipment):
        if not shipment.consignment_id:
            raise ValueError("Shipment does not have a consignment ID.")
        response = requests.get(
            f"{self.base_url}/status_by_consignment/{shipment.consignment_id}",
            headers=self._headers(),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
