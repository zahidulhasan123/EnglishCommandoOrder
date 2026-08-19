from django.core.validators import MinValueValidator
from django.db import models


class CourierProvider(models.TextChoices):
	STEADFAST = "STEADFAST", "Steadfast"


class CourierShipment(models.Model):
	order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="shipments")
	courier = models.CharField(max_length=24, choices=CourierProvider.choices, db_index=True)
	external_order_id = models.CharField(max_length=120, blank=True, db_index=True)
	consignment_id = models.CharField(max_length=120, blank=True, db_index=True)
	tracking_code = models.CharField(max_length=120, blank=True, db_index=True)
	delivery_status = models.CharField(max_length=50, default="CREATED", db_index=True)
	cod_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	raw_response = models.JSONField(default=dict, blank=True)
	error_message = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(fields=["order", "courier"], name="unique_order_courier_shipment"),
		]

	def __str__(self) -> str:
		return f"{self.order.order_number} - {self.courier}"
