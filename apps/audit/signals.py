from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.audit.models import ActivityLog
from apps.customers.models import Customer
from apps.orders.models import Order


@receiver(pre_save, sender=Customer)
def cache_customer_previous(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_state = None
        return
    instance._previous_state = sender.objects.filter(pk=instance.pk).values(
        "name", "phone", "secondary_phone", "address", "city"
    ).first()


@receiver(post_save, sender=Customer)
def log_customer_changes(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            action="customer_created",
            model_name="Customer",
            object_id=str(instance.pk),
            old_value={},
            new_value={
                "name": instance.name,
                "phone": instance.phone,
                "secondary_phone": instance.secondary_phone,
                "address": instance.address,
                "city": instance.city,
            },
        )
        return

    old_state = getattr(instance, "_previous_state", None) or {}
    new_state = {
        "name": instance.name,
        "phone": instance.phone,
        "secondary_phone": instance.secondary_phone,
        "address": instance.address,
        "city": instance.city,
    }
    if old_state != new_state:
        ActivityLog.objects.create(
            action="customer_updated",
            model_name="Customer",
            object_id=str(instance.pk),
            old_value=old_state,
            new_value=new_state,
        )


@receiver(post_save, sender=Order)
def log_order_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            action="order_created",
            model_name="Order",
            object_id=str(instance.pk),
            old_value={},
            new_value={
                "order_number": instance.order_number,
                "status": instance.status,
                "total_amount": str(instance.total_amount),
            },
        )
