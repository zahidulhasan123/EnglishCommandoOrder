from datetime import timedelta

from django import template
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.books.models import Book
from apps.orders.models import Order, OrderStatus

register = template.Library()


@register.simple_tag
def dashboard_metrics():
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def summary(from_date):
        qs = Order.objects.filter(created_at__date__gte=from_date)
        return qs.aggregate(
            orders=Count("id"),
            revenue=Sum("total_amount"),
            delivered=Count("id", filter=Q(status=OrderStatus.DELIVERED)),
            cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
            returned=Count("id", filter=Q(status=OrderStatus.RETURNED)),
        )

    today_qs = Order.objects.filter(created_at__date=today)

    return {
        "today": {
            "orders": today_qs.count(),
            "revenue": today_qs.aggregate(v=Sum("total_amount")).get("v") or 0,
            "delivered": today_qs.filter(status=OrderStatus.DELIVERED).count(),
            "cancelled": today_qs.filter(status=OrderStatus.CANCELLED).count(),
            "returned": today_qs.filter(status=OrderStatus.RETURNED).count(),
            "pending": today_qs.exclude(
                status__in=[OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED]
            ).count(),
        },
        "week": summary(week_start),
        "month": summary(month_start),
        "pipeline": {
            "awaiting_confirmation": Order.objects.filter(status=OrderStatus.NEW).count(),
            "ready_to_ship": Order.objects.filter(status=OrderStatus.READY_TO_SHIP).count(),
            "in_transit": Order.objects.filter(status=OrderStatus.SHIPPED).count(),
            "delivery_failed": Order.objects.filter(status=OrderStatus.DELIVERY_FAILED).count(),
        },
        "low_stock_books": list(Book.objects.filter(active=True, stock_quantity__lte=10).order_by("stock_quantity")[:10]),
    }
