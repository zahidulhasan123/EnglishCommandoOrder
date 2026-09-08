from django.contrib import admin, messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from apps.audit.models import ActivityLog
from apps.courier.models import CourierProvider
from apps.courier.services.courier_service import CourierService
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
from apps.reports.services.export_service import ExportService


class OrderStatusHistoryInline(admin.TabularInline):
	model = OrderStatusHistory
	extra = 0
	can_delete = False
	readonly_fields = ("old_status", "new_status", "changed_by", "note", "changed_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = (
		"order_number",
		"customer_name",
		"customer_phone",
		"customer_address",
		"book",
		"quantity",
		"total_amount",
		"status_badge",
		"courier_status",
		"created_at",
		"quick_send",
	)
	list_filter = (
		"status",
		"payment_status",
		"book",
		"source",
		"campaign",
		"created_at",
	)
	search_fields = (
		"order_number",
		"customer__name",
		"customer__phone",
		"customer__secondary_phone",
		"customer__address",
		"shipments__tracking_code",
		"shipments__consignment_id",
	)
	readonly_fields = ("order_number", "created_at", "updated_at", "courier_actions", "customer_summary")
	list_per_page = 50
	date_hierarchy = "created_at"
	inlines = [OrderStatusHistoryInline]
	actions = [
		"mark_as_confirmed",
		"mark_as_processing",
		"mark_as_ready_to_ship",
		"cancel_selected",
		"send_selected_to_steadfast",
		"export_selected_csv",
		"export_selected_xlsx",
		"print_selected_invoices",
		"print_selected_packing_slips",
	]
	fieldsets = (
		(
			"Customer",
			{
				"fields": (
					"customer",
					"customer_summary",
				)
			},
		),
		(
			"Order",
			{
				"fields": (
					"order_number",
					"book",
					"quantity",
					"unit_price",
					"discount_amount",
					"delivery_charge",
					"total_amount",
				)
			},
		),
		(
			"Status",
			{"fields": ("status", "payment_method", "payment_status", "confirmed_at", "cancelled_at", "delivered_at")},
		),
		(
			"Source",
			{
				"fields": (
					"source",
					"landing_page",
					"landing_page_slug",
					"campaign",
					"utm_source",
					"utm_medium",
					"utm_campaign",
					"utm_term",
					"utm_content",
					"referrer",
					"user_agent",
					"ip_address",
				)
			},
		),
		("Notes", {"fields": ("customer_note", "admin_note")}),
		("Actions", {"fields": ("courier_actions",)}),
		("Meta", {"fields": ("created_at", "updated_at")}),
	)

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		return queryset.select_related("customer", "book").prefetch_related("shipments")

	@admin.display(description="Customer")
	def customer_name(self, obj):
		return obj.customer.name

	@admin.display(description="Phone")
	def customer_phone(self, obj):
		return obj.customer.phone

	@admin.display(description="Address")
	def customer_address(self, obj):
		parts = [obj.customer.address, obj.customer.city]
		return ", ".join(part for part in parts if part)

	@admin.display(description="Status")
	def status_badge(self, obj):
		color = {
			OrderStatus.NEW: "#0d6efd",
			OrderStatus.CONFIRMED: "#198754",
			OrderStatus.PROCESSING: "#0dcaf0",
			OrderStatus.READY_TO_SHIP: "#fd7e14",
			OrderStatus.SHIPPED: "#6f42c1",
			OrderStatus.DELIVERED: "#198754",
			OrderStatus.CANCELLED: "#dc3545",
			OrderStatus.DELIVERY_FAILED: "#6c757d",
			OrderStatus.RETURNED: "#b02a37",
		}.get(obj.status, "#6c757d")
		return format_html(
			'<span style="background:{};color:white;padding:3px 8px;border-radius:10px;">{}</span>',
			color,
			obj.get_status_display(),
		)

	@admin.display(description="Courier")
	def courier_status(self, obj):
		shipment = obj.shipments.first()
		if not shipment:
			return "Not sent"
		return shipment.delivery_status

	@admin.display(description="Quick Action")
	def quick_send(self, obj):
		if obj.shipments.filter(courier=CourierProvider.STEADFAST).exists():
			return "Already sent"
		url = reverse("admin:orders_order_send_steadfast", args=[obj.pk])
		return format_html('<a class="button" href="{}">Send to Steadfast</a>', url)

	@admin.display(description="Customer Summary")
	def customer_summary(self, obj):
		summary = obj.customer.orders.aggregate(
			total_orders=Count("id"),
			delivered=Count("id", filter=Q(status=OrderStatus.DELIVERED)),
			cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
			returned=Count("id", filter=Q(status=OrderStatus.RETURNED)),
			failed=Count("id", filter=Q(status=OrderStatus.DELIVERY_FAILED)),
			active_orders=Count(
				"id",
				filter=~Q(status__in=[OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED]),
			),
			spent=Sum("total_amount"),
		)
		total_orders_url = (
			reverse("admin:orders_order_changelist") + f"?customer__id__exact={obj.customer_id}"
		)
		warning = ""
		if (summary.get("cancelled", 0) or 0) >= 3 or (summary.get("failed", 0) or 0) >= 2:
			warning = format_html(
				"<br/><span style='color:#b02a37;font-weight:700;'>WARNING:</span> "
				"Phone has {} cancellations, {} failed deliveries, {} active orders.",
				summary.get("cancelled", 0),
				summary.get("failed", 0),
				summary.get("active_orders", 0),
			)

		return format_html(
			"<strong>{}</strong><br/>Phone: {}<br/>Address: {}, {}<br/>Previous Orders: <a href='{}'>{}</a><br/>"
			"Delivered: {} | Cancelled: {} | Returned: {} | Failed: {}<br/>"
			"Active Orders: {}<br/>Total Spent: {}{}",
			obj.customer.name,
			obj.customer.phone,
			obj.customer.address,
			obj.customer.city,
			total_orders_url,
			summary.get("total_orders", 0),
			summary.get("delivered", 0),
			summary.get("cancelled", 0),
			summary.get("returned", 0),
			summary.get("failed", 0),
			summary.get("active_orders", 0),
			summary.get("spent") or 0,
			warning,
		)

	@admin.display(description="Courier Actions")
	def courier_actions(self, obj):
		if not obj.pk:
			return "Save order first"
		send_url = reverse("admin:orders_order_send_steadfast", args=[obj.pk])
		invoice_url = reverse("admin:orders_order_print_invoice", args=[obj.pk])
		slip_url = reverse("admin:orders_order_print_packing_slip", args=[obj.pk])
		return format_html(
			'<a class="button" href="{}">Send to Steadfast</a>&nbsp;'
			'<a class="button" href="{}" target="_blank">Print Invoice</a>&nbsp;'
			'<a class="button" href="{}" target="_blank">Packing Slip</a>',
			send_url,
			invoice_url,
			slip_url,
		)

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"<int:order_id>/send-to-steadfast/",
				self.admin_site.admin_view(self.send_to_steadfast_view),
				name="orders_order_send_steadfast",
			),
			path(
				"<int:order_id>/print-invoice/",
				self.admin_site.admin_view(self.print_invoice_view),
				name="orders_order_print_invoice",
			),
			path(
				"<int:order_id>/print-packing-slip/",
				self.admin_site.admin_view(self.print_packing_slip_view),
				name="orders_order_print_packing_slip",
			),
		]
		return custom_urls + urls

	def print_invoice_view(self, request, order_id):
		order = self.get_queryset(request).get(pk=order_id)
		return TemplateResponse(
			request,
			"admin/orders/invoice.html",
			{
				**self.admin_site.each_context(request),
				"title": f"Invoice {order.order_number}",
				"order": order,
			},
		)

	def print_packing_slip_view(self, request, order_id):
		order = self.get_queryset(request).get(pk=order_id)
		shipment = order.shipments.first()
		return TemplateResponse(
			request,
			"admin/orders/packing_slip.html",
			{
				**self.admin_site.each_context(request),
				"title": f"Packing Slip {order.order_number}",
				"order": order,
				"shipment": shipment,
			},
		)

	def send_to_steadfast_view(self, request, order_id):
		order = self.get_queryset(request).get(pk=order_id)
		shipment, created, message = CourierService.create_steadfast_shipment(order)
		level = messages.SUCCESS if created else messages.WARNING
		if shipment.error_message:
			level = messages.ERROR
		self.message_user(request, message, level=level)
		ActivityLog.objects.create(
			user=request.user,
			action="send_to_steadfast",
			model_name="Order",
			object_id=str(order.pk),
			old_value={},
			new_value={
				"shipment_id": shipment.pk,
				"consignment_id": shipment.consignment_id,
				"tracking_code": shipment.tracking_code,
			},
		)
		return HttpResponseRedirect(reverse("admin:orders_order_change", args=[order.pk]))

	@admin.action(description="Mark selected as Confirmed")
	def mark_as_confirmed(self, request, queryset):
		self._transition_many(request, queryset, OrderStatus.CONFIRMED)

	@admin.action(description="Mark selected as Processing")
	def mark_as_processing(self, request, queryset):
		self._transition_many(request, queryset, OrderStatus.PROCESSING)

	@admin.action(description="Mark selected as Ready to Ship")
	def mark_as_ready_to_ship(self, request, queryset):
		self._transition_many(request, queryset, OrderStatus.READY_TO_SHIP)

	@admin.action(description="Cancel selected orders")
	def cancel_selected(self, request, queryset):
		self._transition_many(request, queryset, OrderStatus.CANCELLED)

	@admin.action(description="Send selected orders to Steadfast")
	def send_selected_to_steadfast(self, request, queryset):
		success = 0
		warnings = 0
		errors = 0
		for order in queryset.select_related("customer", "book"):
			shipment, created, _ = CourierService.create_steadfast_shipment(order)
			if shipment.error_message:
				errors += 1
			elif created:
				success += 1
			else:
				warnings += 1
		self.message_user(
			request,
			f"Courier summary: sent={success}, already_sent={warnings}, failed={errors}",
			level=messages.INFO,
		)

	def _transition_many(self, request, queryset, target_status: str):
		updated = 0
		skipped = 0
		for order in queryset:
			if order.can_transition(target_status):
				order.transition_to(target_status, by_user=request.user)
				updated += 1
			else:
				skipped += 1
		self.message_user(request, f"Updated {updated} order(s), skipped {skipped} invalid transition(s).")

	@admin.action(description="Export selected orders (CSV)")
	def export_selected_csv(self, request, queryset):
		return ExportService.export_orders_csv(queryset)

	@admin.action(description="Export selected orders (XLSX)")
	def export_selected_xlsx(self, request, queryset):
		return ExportService.export_orders_xlsx(queryset)

	@admin.action(description="Print selected invoices")
	def print_selected_invoices(self, request, queryset):
		ids = ",".join([str(order.pk) for order in queryset])
		url = reverse("admin:orders_order_changelist") + f"?print_invoices={ids}"
		return HttpResponseRedirect(url)

	@admin.action(description="Print selected packing slips")
	def print_selected_packing_slips(self, request, queryset):
		ids = ",".join([str(order.pk) for order in queryset])
		url = reverse("admin:orders_order_changelist") + f"?print_packing_slips={ids}"
		return HttpResponseRedirect(url)

	def changelist_view(self, request, extra_context=None):
		invoice_ids = request.GET.get("print_invoices")
		if invoice_ids:
			orders = self.get_queryset(request).filter(pk__in=[int(i) for i in invoice_ids.split(",") if i])
			return TemplateResponse(
				request,
				"admin/orders/bulk_invoices.html",
				{
					**self.admin_site.each_context(request),
					"title": "Bulk Invoices",
					"orders": orders,
				},
			)

		slip_ids = request.GET.get("print_packing_slips")
		if slip_ids:
			orders = self.get_queryset(request).filter(pk__in=[int(i) for i in slip_ids.split(",") if i])
			return TemplateResponse(
				request,
				"admin/orders/bulk_packing_slips.html",
				{
					**self.admin_site.each_context(request),
					"title": "Bulk Packing Slips",
					"orders": orders,
				},
			)

		return super().changelist_view(request, extra_context)
