import re

def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    return re.sub(r'\D', '', phone)

def find_customer_by_phone(phone: str):
    """
    Try to find a customer by phone, ignoring formatting (compare digits only).
    Returns Customer or None. This iterates — fine for small DB; consider storing normalized_phone for scale.
    """
    norm = normalize_phone(phone)
    if not norm:
        return None
    from .models import Customer
    for c in Customer.objects.all():
        if normalize_phone(c.phone) == norm:
            return c
    return None
