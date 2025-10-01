from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def vnd(value):
    """Định dạng 100000 -> 100,000 (không thêm đơn vị)."""
    try:
        n = int(Decimal(str(value)))
        return f"{n:,}"  # dùng dấu phẩy
    except Exception:
        return value