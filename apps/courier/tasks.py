from celery import shared_task

from apps.courier.models import CourierProvider, CourierShipment
from apps.courier.services.steadfast import SteadfastClient


@shared_task
def sync_steadfast_statuses():
    client = SteadfastClient()
    shipments = CourierShipment.objects.filter(courier=CourierProvider.STEADFAST).exclude(consignment_id="")
    for shipment in shipments.iterator(chunk_size=200):
        try:
            payload = client.get_status(shipment)
            shipment.delivery_status = str(payload.get("delivery_status") or payload.get("status") or shipment.delivery_status)
            shipment.raw_response = payload
            shipment.error_message = ""
            shipment.save(update_fields=["delivery_status", "raw_response", "error_message", "updated_at"])
        except Exception as exc:
            shipment.error_message = str(exc)
            shipment.save(update_fields=["error_message", "updated_at"])
