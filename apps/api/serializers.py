from rest_framework import serializers

from apps.books.models import Book
from apps.orders.models import Order


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "description",
            "cover_image",
            "sku",
            "price",
            "discount_price",
            "stock_quantity",
            "active",
        ]


class OrderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    secondary_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)
    book_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    customer_note = serializers.CharField(required=False, allow_blank=True)
    delivery_charge = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    source = serializers.CharField(max_length=120, required=False, allow_blank=True)
    landing_page = serializers.CharField(max_length=255, required=False, allow_blank=True)
    landing_page_slug = serializers.CharField(max_length=255, required=False, allow_blank=True)
    campaign = serializers.CharField(max_length=255, required=False, allow_blank=True)
    utm_source = serializers.CharField(max_length=120, required=False, allow_blank=True)
    utm_medium = serializers.CharField(max_length=120, required=False, allow_blank=True)
    utm_campaign = serializers.CharField(max_length=120, required=False, allow_blank=True)
    utm_term = serializers.CharField(max_length=120, required=False, allow_blank=True)
    utm_content = serializers.CharField(max_length=120, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class OrderPublicSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")
    customer_phone = serializers.CharField(source="customer.phone")
    book_title = serializers.CharField(source="book.title")

    class Meta:
        model = Order
        fields = [
            "order_number",
            "customer_name",
            "customer_phone",
            "book_title",
            "quantity",
            "total_amount",
            "status",
            "created_at",
            "delivered_at",
        ]
