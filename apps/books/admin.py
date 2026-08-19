from django.contrib import admin

from apps.books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"sku",
		"price",
		"discount_price",
		"stock_quantity",
		"active",
		"updated_at",
	)
	list_filter = ("active", "created_at")
	search_fields = ("title", "sku", "author")
	list_per_page = 50
	prepopulated_fields = {"slug": ("title",)}
