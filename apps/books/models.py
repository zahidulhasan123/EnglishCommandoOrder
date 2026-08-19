from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Book(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(max_length=255, unique=True, db_index=True)
	author = models.CharField(max_length=255, blank=True)
	description = models.TextField(blank=True)
	cover_image = models.ImageField(upload_to="books/covers/", blank=True, null=True)
	sku = models.CharField(max_length=64, unique=True, db_index=True)
	price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
	discount_price = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		blank=True,
		null=True,
		validators=[MinValueValidator(Decimal("0.00"))],
	)
	stock_quantity = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=10)
	active = models.BooleanField(default=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.CheckConstraint(
				condition=models.Q(discount_price__isnull=True) | models.Q(discount_price__lte=models.F("price")),
				name="book_discount_lte_price",
			)
		]

	def __str__(self) -> str:
		return f"{self.title} ({self.sku})"

	@property
	def effective_price(self) -> Decimal:
		if self.discount_price is not None:
			return self.discount_price
		return self.price

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		super().save(*args, **kwargs)
