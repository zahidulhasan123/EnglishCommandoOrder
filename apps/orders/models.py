from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.books.models import Book
from apps.customers.models import Customer


class OrderStatus(models.TextChoices):
	NEW = "NEW", "New"
	CONFIRMED = "CONFIRMED", "Confirmed"
	PROCESSING = "PROCESSING", "Processing"
	READY_TO_SHIP = "READY_TO_SHIP", "Ready to Ship"
	SHIPPED = "SHIPPED", "Shipped"
	DELIVERED = "DELIVERED", "Delivered"
	CANCELLED = "CANCELLED", "Cancelled"
	DELIVERY_FAILED = "DELIVERY_FAILED", "Delivery Failed"
	RETURNED = "RETURNED", "Returned"


class PaymentMethod(models.TextChoices):
	COD = "COD", "Cash on Delivery"


class PaymentStatus(models.TextChoices):
	UNPAID = "UNPAID", "Unpaid"
	PAID = "PAID", "Paid"
	REFUNDED = "REFUNDED", "Refunded"


ALLOWED_TRANSITIONS = {
	OrderStatus.NEW: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
	OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
	OrderStatus.PROCESSING: {OrderStatus.READY_TO_SHIP, OrderStatus.CANCELLED},
	OrderStatus.READY_TO_SHIP: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
	OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.DELIVERY_FAILED, OrderStatus.RETURNED},
	OrderStatus.DELIVERED: set(),
	OrderStatus.CANCELLED: set(),
	OrderStatus.DELIVERY_FAILED: set(),
	OrderStatus.RETURNED: set(),
}


class Order(models.Model):
	order_number = models.CharField(max_length=32, unique=True, db_index=True)
	idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
	customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
	book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="orders")
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
	discount_amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
		validators=[MinValueValidator(Decimal("0.00"))],
	)
	delivery_charge = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
		validators=[MinValueValidator(Decimal("0.00"))],
	)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
	customer_note = models.TextField(blank=True)
	admin_note = models.TextField(blank=True)
	status = models.CharField(max_length=24, choices=OrderStatus.choices, default=OrderStatus.NEW, db_index=True)
	payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD)
	payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
	source = models.CharField(max_length=120, blank=True, db_index=True)
	landing_page = models.CharField(max_length=255, blank=True, db_index=True)
	landing_page_slug = models.SlugField(max_length=255, blank=True, db_index=True)
	campaign = models.CharField(max_length=255, blank=True, db_index=True)
	utm_source = models.CharField(max_length=120, blank=True, db_index=True)
	utm_medium = models.CharField(max_length=120, blank=True, db_index=True)
	utm_campaign = models.CharField(max_length=120, blank=True, db_index=True)
	utm_term = models.CharField(max_length=120, blank=True)
	utm_content = models.CharField(max_length=120, blank=True)
	referrer = models.URLField(blank=True)
	user_agent = models.TextField(blank=True)
	ip_address = models.GenericIPAddressField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)
	confirmed_at = models.DateTimeField(blank=True, null=True)
	cancelled_at = models.DateTimeField(blank=True, null=True)
	delivered_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["idempotency_key", "created_at"]),
			models.Index(fields=["status", "created_at"]),
			models.Index(fields=["landing_page", "campaign"]),
			models.Index(fields=["utm_source", "utm_campaign"]),
		]

	def __str__(self) -> str:
		return self.order_number

	@property
	def subtotal(self) -> Decimal:
		return self.unit_price * self.quantity

	def clean(self):
		expected_total = self.subtotal - self.discount_amount + self.delivery_charge
		if self.total_amount != expected_total:
			raise ValidationError({"total_amount": "Total amount does not match calculated amount."})

	def can_transition(self, new_status: str) -> bool:
		return new_status in ALLOWED_TRANSITIONS.get(self.status, set())

	def transition_to(self, new_status: str, by_user=None, note: str = "") -> None:
		if new_status == self.status:
			return
		if not self.can_transition(new_status):
			raise ValidationError(f"Invalid status transition: {self.status} -> {new_status}")

		old_status = self.status
		self.status = new_status
		now = timezone.now()

		if new_status == OrderStatus.CONFIRMED and not self.confirmed_at:
			self.confirmed_at = now
		if new_status == OrderStatus.CANCELLED:
			self.cancelled_at = now
		if new_status == OrderStatus.DELIVERED:
			self.delivered_at = now

		self.save(update_fields=["status", "confirmed_at", "cancelled_at", "delivered_at", "updated_at"])
		OrderStatusHistory.objects.create(
			order=self,
			old_status=old_status,
			new_status=new_status,
			changed_by=by_user,
			note=note,
		)


class OrderStatusHistory(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
	old_status = models.CharField(max_length=24, choices=OrderStatus.choices)
	new_status = models.CharField(max_length=24, choices=OrderStatus.choices)
	changed_by = models.ForeignKey(
		"auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_status_changes"
	)
	note = models.CharField(max_length=255, blank=True)
	changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-changed_at"]
