from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.books.models import Book
from apps.customers.services.customer_service import CustomerService
from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.orders.services.order_number import generate_order_number


class OrderService:
    DUPLICATE_WINDOW_SECONDS = 120

    @staticmethod
    def _find_recent_duplicate(*, customer_id: int, book_id: int, quantity: int):
        since = timezone.now() - timedelta(seconds=OrderService.DUPLICATE_WINDOW_SECONDS)
        return (
            Order.objects.filter(
                customer_id=customer_id,
                book_id=book_id,
                quantity=quantity,
                created_at__gte=since,
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    @transaction.atomic
    def create_order(*, payload: dict, meta: dict) -> Order:
        book = Book.objects.select_for_update().filter(id=payload["book_id"], active=True).first()
        if not book:
            raise ValueError("Selected book is not available.")

        quantity = int(payload["quantity"])
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        customer = CustomerService.get_or_create_customer(
            name=payload["name"],
            phone=payload["phone"],
            secondary_phone=payload.get("secondary_phone", ""),
            address=payload["address"],
            city=payload.get("city", ""),
        )

        idempotency_key = (meta.get("idempotency_key") or "").strip()
        if idempotency_key:
            existing = Order.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing

        recent_duplicate = OrderService._find_recent_duplicate(
            customer_id=customer.pk,
            book_id=book.pk,
            quantity=quantity,
        )
        if recent_duplicate:
            return recent_duplicate

        unit_price = book.effective_price
        subtotal = unit_price * quantity
        discount_amount = Decimal(payload.get("discount_amount", "0") or "0")
        delivery_charge = Decimal(payload.get("delivery_charge", "0") or "0")
        total_amount = subtotal - discount_amount + delivery_charge

        if book.stock_quantity < quantity:
            raise ValueError("Insufficient stock.")

        order = Order.objects.create(
            order_number=generate_order_number(),
            idempotency_key=idempotency_key,
            customer=customer,
            book=book,
            quantity=quantity,
            unit_price=unit_price,
            discount_amount=discount_amount,
            delivery_charge=delivery_charge,
            total_amount=total_amount,
            customer_note=payload.get("customer_note", ""),
            payment_method=PaymentMethod.COD,
            payment_status=PaymentStatus.UNPAID,
            source=meta.get("source", ""),
            landing_page=meta.get("landing_page", ""),
            landing_page_slug=meta.get("landing_page_slug", ""),
            campaign=meta.get("campaign", ""),
            utm_source=meta.get("utm_source", ""),
            utm_medium=meta.get("utm_medium", ""),
            utm_campaign=meta.get("utm_campaign", ""),
            utm_term=meta.get("utm_term", ""),
            utm_content=meta.get("utm_content", ""),
            referrer=meta.get("referrer", ""),
            user_agent=meta.get("user_agent", ""),
            ip_address=meta.get("ip_address"),
        )

        book.stock_quantity = book.stock_quantity - quantity
        book.save(update_fields=["stock_quantity", "updated_at"])
        return order
