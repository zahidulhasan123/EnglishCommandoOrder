from django.contrib import admin

from apps.courier.models import CourierShipment


@admin.register(CourierShipment)
class CourierShipmentAdmin(admin.ModelAdmin):
	list_display = (
		"order",
		"courier",
		"consignment_id",
		"tracking_code",
		"delivery_status",
		"created_at",
	)
	list_filter = ("courier", "delivery_status", "created_at")
	search_fields = ("order__order_number", "consignment_id", "tracking_code", "external_order_id")
	list_per_page = 50
