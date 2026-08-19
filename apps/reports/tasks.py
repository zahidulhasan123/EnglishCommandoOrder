from celery import shared_task

from apps.orders.models import Order
from apps.reports.services.export_service import ExportService


@shared_task
def export_orders_csv_task(order_ids):
    queryset = Order.objects.filter(id__in=order_ids)
    # Placeholder return value; storing files can be added with object storage integration.
    response = ExportService.export_orders_csv(queryset)
    return {"content_type": response["Content-Type"], "size": len(response.content)}
