from unittest.mock import patch
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.books.models import Book
from apps.courier.models import CourierShipment
from apps.courier.services.courier_service import CourierService
from apps.customers.models import Customer
from apps.orders.models import Order, OrderStatus


class OrderApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.book = Book.objects.create(
			title="Python Fundamentals",
			slug="python-fundamentals",
			sku="PY-001",
			price="500.00",
			discount_price="450.00",
			stock_quantity=100,
			active=True,
		)

	def test_order_creation_calculates_price_from_db(self):
		payload = {
			"name": "Rahim",
			"phone": "01700000000",
			"address": "Dhaka",
			"book_id": self.book.id,
			"quantity": 2,
			"delivery_charge": "60.00",
			"discount_amount": "0.00",
		}
		response = self.client.post("/api/orders/", payload, format="json")
		self.assertEqual(response.status_code, 201)

		order = Order.objects.get(order_number=response.data["order_number"])
		self.assertEqual(order.unit_price, Decimal("450.00"))
		self.assertEqual(order.total_amount, Decimal("960.00"))

	def test_order_reuses_existing_customer_by_phone(self):
		Customer.objects.create(name="Rahim", phone="01700000000", address="A")
		payload = {
			"name": "Rahim Updated",
			"phone": "01700000000",
			"address": "B",
			"book_id": self.book.id,
			"quantity": 1,
		}
		response = self.client.post("/api/orders/", payload, format="json")
		self.assertEqual(response.status_code, 201)
		self.assertEqual(Customer.objects.count(), 1)
		self.assertEqual(Customer.objects.first().address, "B")

	def test_order_create_is_idempotent_with_header_key(self):
		payload = {
			"name": "Rahim",
			"phone": "01700000000",
			"address": "Dhaka",
			"book_id": self.book.id,
			"quantity": 1,
		}
		headers = {"HTTP_X_IDEMPOTENCY_KEY": "same-request-key-1"}
		response1 = self.client.post("/api/orders/", payload, format="json", **headers)
		response2 = self.client.post("/api/orders/", payload, format="json", **headers)

		self.assertEqual(response1.status_code, 201)
		self.assertEqual(response2.status_code, 201)
		self.assertEqual(response1.data["order_number"], response2.data["order_number"])
		self.assertEqual(Order.objects.count(), 1)

	def test_order_create_prevents_double_click_duplicate_window(self):
		payload = {
			"name": "Rahim",
			"phone": "01700000000",
			"address": "Dhaka",
			"book_id": self.book.id,
			"quantity": 1,
		}
		response1 = self.client.post("/api/orders/", payload, format="json")
		response2 = self.client.post("/api/orders/", payload, format="json")

		self.assertEqual(response1.status_code, 201)
		self.assertEqual(response2.status_code, 201)
		self.assertEqual(response1.data["order_number"], response2.data["order_number"])
		self.assertEqual(Order.objects.count(), 1)


class OrderWorkflowTests(TestCase):
	def setUp(self):
		self.book = Book.objects.create(
			title="Django Mastery",
			slug="django-mastery",
			sku="DJ-001",
			price="600.00",
			stock_quantity=50,
			active=True,
		)
		self.customer = Customer.objects.create(name="Karim", phone="01711111111", address="Dhaka")
		self.order = Order.objects.create(
			order_number="ORD-20260814-000001",
			customer=self.customer,
			book=self.book,
			quantity=1,
			unit_price="600.00",
			discount_amount="0.00",
			delivery_charge="60.00",
			total_amount="660.00",
		)
		self.user = get_user_model().objects.create_user(username="admin", password="pass")

	def test_status_transition_rules(self):
		self.assertTrue(self.order.can_transition(OrderStatus.CONFIRMED))
		self.order.transition_to(OrderStatus.CONFIRMED, by_user=self.user)
		self.assertEqual(self.order.status, OrderStatus.CONFIRMED)
		self.assertFalse(self.order.can_transition(OrderStatus.DELIVERED))

	@patch("apps.courier.services.steadfast.SteadfastClient.create_shipment")
	def test_courier_submission_idempotent(self, mock_create):
		self.order.transition_to(OrderStatus.CONFIRMED, by_user=self.user)
		mock_create.return_value = {
			"order_id": "EXT-1",
			"status": "created",
			"consignment": {"consignment_id": "C-1", "tracking_code": "T-1"},
		}
		shipment1, created1, _ = CourierService.create_steadfast_shipment(self.order)
		shipment2, created2, _ = CourierService.create_steadfast_shipment(self.order)

		self.assertTrue(created1)
		self.assertFalse(created2)
		self.assertEqual(shipment1.pk, shipment2.pk)
		self.assertEqual(CourierShipment.objects.count(), 1)
