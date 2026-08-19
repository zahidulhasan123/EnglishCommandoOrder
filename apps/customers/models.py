from django.db import models

from apps.core.utils import normalize_bd_phone


class Customer(models.Model):
	name = models.CharField(max_length=255)
	phone = models.CharField(max_length=20, db_index=True)
	normalized_phone = models.CharField(max_length=20, unique=True, db_index=True)
	secondary_phone = models.CharField(max_length=20, blank=True)
	normalized_secondary_phone = models.CharField(max_length=20, blank=True, db_index=True)
	address = models.TextField()
	city = models.CharField(max_length=120, blank=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.name} ({self.phone})"

	def save(self, *args, **kwargs):
		self.normalized_phone = normalize_bd_phone(self.phone)
		self.normalized_secondary_phone = normalize_bd_phone(self.secondary_phone) if self.secondary_phone else ""
		super().save(*args, **kwargs)
