from apps.core.utils import normalize_bd_phone
from apps.customers.models import Customer


class CustomerService:
    @staticmethod
    def get_or_create_customer(*, name: str, phone: str, secondary_phone: str = "", address: str, city: str = "") -> Customer:
        normalized_phone = normalize_bd_phone(phone)
        customer = Customer.objects.filter(normalized_phone=normalized_phone).first()
        if customer:
            customer.name = name or customer.name
            customer.phone = phone or customer.phone
            customer.secondary_phone = secondary_phone or customer.secondary_phone
            customer.address = address or customer.address
            customer.city = city or customer.city
            customer.save()
            return customer

        return Customer.objects.create(
            name=name,
            phone=phone,
            secondary_phone=secondary_phone,
            address=address,
            city=city,
        )
