from django.urls import path

from apps.api.views import (
    BookDetailAPIView,
    BookListAPIView,
    OrderCreateAPIView,
    OrderDetailPublicAPIView,
)

urlpatterns = [
    path("books/", BookListAPIView.as_view(), name="book-list"),
    path("books/<slug:slug>/", BookDetailAPIView.as_view(), name="book-detail"),
    path("orders/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/<str:order_number>/", OrderDetailPublicAPIView.as_view(), name="order-detail"),
]
