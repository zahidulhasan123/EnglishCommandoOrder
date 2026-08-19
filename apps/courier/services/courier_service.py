from django.db import IntegrityError, transaction

from apps.courier.models import CourierProvider, CourierShipment
from apps.courier.services.steadfast import SteadfastClient
from apps.orders.models import OrderStatus


class CourierService:
    @staticmethod
    @transaction.atomic
    def create_steadfast_shipment(order):
        if order.status not in {OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.READY_TO_SHIP}:
            raise ValueError("Only confirmed/processing/ready-to-ship orders can be sent to courier.")

        existing = CourierShipment.objects.select_for_update().filter(
            order=order,
            courier=CourierProvider.STEADFAST,
        ).first()
        if existing and existing.consignment_id:
            return existing, False, "Already sent to Steadfast"

        if existing is None:
            existing = CourierShipment.objects.create(
                order=order,
                courier=CourierProvider.STEADFAST,
                cod_amount=order.total_amount,
                raw_response={},
            )

        client = SteadfastClient()
        try:
            result = client.create_shipment(order)
            existing.external_order_id = str(result.get("order_id", ""))
            existing.consignment_id = str(result.get("consignment", {}).get("consignment_id", ""))
            existing.tracking_code = str(result.get("consignment", {}).get("tracking_code", ""))
            existing.delivery_status = str(result.get("status", "CREATED"))
            existing.raw_response = result
            existing.error_message = ""
            existing.save()
            return existing, True, "Sent to Steadfast"
        except IntegrityError:
            shipment = CourierShipment.objects.get(order=order, courier=CourierProvider.STEADFAST)
            return shipment, False, "Already sent to Steadfast"
        except Exception as exc:
            existing.error_message = str(exc)
            existing.save(update_fields=["error_message", "updated_at"])
            return existing, False, f"Courier submission failed: {exc}"
