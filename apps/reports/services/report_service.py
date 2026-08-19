from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.orders.models import Order, OrderStatus


class ReportService:
    @staticmethod
    def _base_summary(queryset):
        shipped = queryset.filter(status=OrderStatus.SHIPPED)
        shipped_count = shipped.count()
        delivered_count = queryset.filter(status=OrderStatus.DELIVERED).count()
        cancelled_count = queryset.filter(status=OrderStatus.CANCELLED).count()
        returned_count = queryset.filter(status=OrderStatus.RETURNED).count()
        failed_count = queryset.filter(status=OrderStatus.DELIVERY_FAILED).count()
        total_orders = queryset.count()

        aggregate = queryset.aggregate(
            gross_sales=Sum("total_amount"),
            total_discount=Sum("discount_amount"),
            total_delivery_charge=Sum("delivery_charge"),
            books_sold=Sum("quantity"),
        )
        gross_sales = aggregate.get("gross_sales") or 0

        return {
            "total_orders": total_orders,
            "delivered": delivered_count,
            "cancelled": cancelled_count,
            "returned": returned_count,
            "delivery_failed": failed_count,
            "gross_sales": gross_sales,
            "total_discount": aggregate.get("total_discount") or 0,
            "total_delivery_charge": aggregate.get("total_delivery_charge") or 0,
            "books_sold": aggregate.get("books_sold") or 0,
            "avg_order_value": (gross_sales / total_orders) if total_orders else 0,
            "delivery_success_rate": (delivered_count / shipped_count) if shipped_count else 0,
            "cancellation_rate": (cancelled_count / total_orders) if total_orders else 0,
            "return_rate": (returned_count / shipped_count) if shipped_count else 0,
            "failed_delivery_rate": (failed_count / shipped_count) if shipped_count else 0,
        }

    @staticmethod
    def for_date(target_date: date):
        qs = Order.objects.filter(created_at__date=target_date).select_related("book", "customer")
        return {
            "summary": ReportService._base_summary(qs),
            "orders_by_book": list(
                qs.values("book__title")
                .annotate(orders=Count("id"), units=Sum("quantity"), sales=Sum("total_amount"))
                .order_by("-orders")
            ),
            "orders_by_landing": list(
                qs.values("landing_page")
                .annotate(orders=Count("id"), sales=Sum("total_amount"))
                .order_by("-orders")
            ),
            "orders_by_campaign": list(
                qs.values("campaign")
                .annotate(orders=Count("id"), sales=Sum("total_amount"))
                .order_by("-orders")
            ),
            "orders_by_source": list(
                qs.values("source")
                .annotate(orders=Count("id"), sales=Sum("total_amount"))
                .order_by("-orders")
            ),
        }

    @staticmethod
    def weekly(current_week=True, start_date=None, end_date=None):
        if start_date and end_date:
            start = start_date
            end = end_date
        else:
            today = timezone.localdate()
            start = today - timedelta(days=today.weekday())
            if not current_week:
                start = start - timedelta(days=7)
            end = start + timedelta(days=6)

        qs = Order.objects.filter(created_at__date__range=[start, end])
        daily = list(
            qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                orders=Count("id"),
                books=Sum("quantity"),
                sales=Sum("total_amount"),
                delivered=Count("id", filter=Q(status=OrderStatus.DELIVERED)),
                cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
            )
            .order_by("day")
        )

        return {
            "range": {"start": start, "end": end},
            "summary": ReportService._base_summary(qs),
            "daily_breakdown": daily,
        }

    @staticmethod
    def monthly(year: int, month: int):
        qs = Order.objects.filter(created_at__year=year, created_at__month=month)
        return {
            "summary": ReportService._base_summary(qs),
            "top_books": list(
                qs.values("book__title").annotate(orders=Count("id"), units=Sum("quantity")).order_by("-orders")[:10]
            ),
            "top_landing_pages": list(
                qs.values("landing_page").annotate(orders=Count("id"), sales=Sum("total_amount")).order_by("-orders")[:10]
            ),
            "top_campaigns": list(
                qs.values("campaign").annotate(orders=Count("id"), sales=Sum("total_amount")).order_by("-orders")[:10]
            ),
            "top_cities": list(qs.values("customer__city").annotate(orders=Count("id")).order_by("-orders")[:10]),
        }

    @staticmethod
    def custom_range(start_date: date, end_date: date):
        qs = Order.objects.filter(created_at__date__range=[start_date, end_date])
        return {
            "range": {"start": start_date, "end": end_date},
            "summary": ReportService._base_summary(qs),
        }
