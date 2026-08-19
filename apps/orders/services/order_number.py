from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order


def generate_order_number() -> str:
    today = timezone.localdate()
    prefix = f"ORD-{today.strftime('%Y%m%d')}"
    with transaction.atomic():
        count_today = Order.objects.select_for_update().filter(order_number__startswith=prefix).count() + 1
    return f"{prefix}-{count_today:06d}"
