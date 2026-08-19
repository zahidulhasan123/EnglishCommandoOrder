from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "ORDER_MANAGER": [
        "view_order",
        "change_order",
        "view_customer",
        "change_customer",
        "add_orderstatushistory",
        "view_couriershipment",
        "add_couriershipment",
        "change_couriershipment",
    ],
    "COURIER_MANAGER": [
        "view_order",
        "view_couriershipment",
        "add_couriershipment",
        "change_couriershipment",
    ],
    "BOOK_MANAGER": [
        "view_book",
        "add_book",
        "change_book",
    ],
    "REPORT_MANAGER": [
        "view_order",
        "view_book",
        "view_customer",
        "view_couriershipment",
    ],
}


class Command(BaseCommand):
    help = "Create and assign standard operational roles"

    def handle(self, *args, **options):
        for role_name, codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            permissions = Permission.objects.filter(codename__in=codenames)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Configured group: {role_name}"))

        self.stdout.write(self.style.SUCCESS("Role bootstrap complete."))
