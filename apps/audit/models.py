from django.db import models


class ActivityLog(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
	action = models.CharField(max_length=120)
	model_name = models.CharField(max_length=120, db_index=True)
	object_id = models.CharField(max_length=64, db_index=True)
	old_value = models.JSONField(default=dict, blank=True)
	new_value = models.JSONField(default=dict, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-timestamp"]

	def __str__(self) -> str:
		return f"{self.timestamp} {self.model_name}:{self.object_id} {self.action}"
