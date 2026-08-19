from django.contrib import admin

from apps.audit.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "user", "action", "model_name", "object_id")
	list_filter = ("action", "model_name", "timestamp")
	search_fields = ("object_id", "model_name", "action")
	readonly_fields = ("timestamp",)
	list_per_page = 50
