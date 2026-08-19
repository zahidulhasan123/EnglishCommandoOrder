from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import BookSerializer, OrderCreateSerializer, OrderPublicSerializer
from apps.books.models import Book
from apps.orders.models import Order
from apps.orders.services.order_service import OrderService


class BookListAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookSerializer
    queryset = Book.objects.filter(active=True).order_by("title")


class BookDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookSerializer
    lookup_field = "slug"
    queryset = Book.objects.filter(active=True)


class OrderCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "order_create"

    @extend_schema(request=OrderCreateSerializer, responses={201: OrderPublicSerializer})
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_data = serializer.validated_data
        idempotency_key = request.headers.get("X-Idempotency-Key") or request_data.get("idempotency_key", "")
        meta = {
            "source": request_data.get("source", ""),
            "landing_page": request_data.get("landing_page", ""),
            "landing_page_slug": request_data.get("landing_page_slug") or slugify(request_data.get("landing_page", "")),
            "campaign": request_data.get("campaign", ""),
            "utm_source": request_data.get("utm_source", ""),
            "utm_medium": request_data.get("utm_medium", ""),
            "utm_campaign": request_data.get("utm_campaign", ""),
            "utm_term": request_data.get("utm_term", ""),
            "utm_content": request_data.get("utm_content", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": request.META.get("REMOTE_ADDR"),
            "idempotency_key": idempotency_key,
        }

        try:
            order = OrderService.create_order(payload=request_data, meta=meta)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderPublicSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailPublicAPIView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderPublicSerializer
    lookup_field = "order_number"
    queryset = Order.objects.select_related("customer", "book")
