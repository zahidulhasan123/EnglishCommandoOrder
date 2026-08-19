from django.contrib import admin
from django.db.models import Count, Max, Sum

from apps.customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"phone",
		"secondary_phone",
		"city",
		"total_orders",
		"total_spent",
		"last_order_date",
	)
	search_fields = ("name", "phone", "secondary_phone", "address")
	list_per_page = 50

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		return queryset.annotate(
			total_orders_count=Count("orders", distinct=True),
			spent_total=Sum("orders__total_amount"),
			latest_order=Max("orders__created_at"),
		)

	@admin.display(ordering="total_orders_count")
	def total_orders(self, obj):
		return obj.total_orders_count or 0

	@admin.display(ordering="spent_total")
	def total_spent(self, obj):
		return obj.spent_total or 0

	@admin.display(ordering="latest_order", description="Last order")
	def last_order_date(self, obj):
		return obj.latest_order
