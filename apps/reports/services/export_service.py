import csv
from io import BytesIO, StringIO

from django.http import HttpResponse
from openpyxl import Workbook


class ExportService:
    @staticmethod
    def export_orders_csv(queryset):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Order Number",
                "Customer",
                "Phone",
                "Book",
                "Quantity",
                "Amount",
                "Status",
                "Courier",
                "Tracking",
                "Created Date",
                "Delivered Date",
                "Source",
                "Campaign",
            ]
        )

        for order in queryset.select_related("customer", "book").prefetch_related("shipments"):
            shipment = order.shipments.first()
            writer.writerow(
                [
                    order.order_number,
                    order.customer.name,
                    order.customer.phone,
                    order.book.title,
                    order.quantity,
                    order.total_amount,
                    order.status,
                    shipment.courier if shipment else "",
                    shipment.tracking_code if shipment else "",
                    order.created_at,
                    order.delivered_at,
                    order.source,
                    order.campaign,
                ]
            )

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        return response

    @staticmethod
    def export_orders_xlsx(queryset):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Orders"
        sheet.append(
            [
                "Order Number",
                "Customer",
                "Phone",
                "Book",
                "Quantity",
                "Amount",
                "Status",
                "Courier",
                "Tracking",
                "Created Date",
                "Delivered Date",
                "Source",
                "Campaign",
            ]
        )

        for order in queryset.select_related("customer", "book").prefetch_related("shipments"):
            shipment = order.shipments.first()
            sheet.append(
                [
                    order.order_number,
                    order.customer.name,
                    order.customer.phone,
                    order.book.title,
                    order.quantity,
                    float(order.total_amount),
                    order.status,
                    shipment.courier if shipment else "",
                    shipment.tracking_code if shipment else "",
                    str(order.created_at),
                    str(order.delivered_at or ""),
                    order.source,
                    order.campaign,
                ]
            )

        stream = BytesIO()
        workbook.save(stream)
        response = HttpResponse(
            stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'
        return response
