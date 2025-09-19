
from decimal import Decimal
from django.utils import timezone
from orders.models import Voucher, VoucherRedemption

def _norm(code: str) -> str:
    return (code or "").strip().upper()

def check_voucher(request, subtotal: Decimal, code: str):
    """Return (ok, discount, msg, voucher)"""
    code = _norm(code)
    if not code:
        return (False, Decimal("0"), "Vui lòng nhập mã.", None)
    try:
        v = Voucher.objects.get(code__iexact=code, is_active=True)
    except Voucher.DoesNotExist:
        return (False, Decimal("0"), "Mã không tồn tại hoặc đã ngừng.", None)

    now = timezone.now()
    if v.start_at and now < v.start_at: return (False, Decimal("0"), "Mã chưa đến thời gian áp dụng.", None)
    if v.end_at and now > v.end_at:     return (False, Decimal("0"), "Mã đã hết hạn.", None)
    if subtotal < v.min_order_total:    return (False, Decimal("0"), f"Đơn tối thiểu {v.min_order_total:,.0f}đ.", None)

    if v.usage_limit is not None and VoucherRedemption.objects.filter(voucher=v).count() >= v.usage_limit:
        return (False, Decimal("0"), "Mã đã hết lượt sử dụng.", None)

    if request.user.is_authenticated:
        used = VoucherRedemption.objects.filter(voucher=v, user=request.user).count()
        if used >= v.per_user_limit:
            return (False, Decimal("0"), "Bạn đã dùng mã này tối đa số lần cho phép.", None)

    # Tính discount
    if v.discount_type == Voucher.PERCENT:
        discount = (subtotal * v.amount / Decimal("100")).quantize(Decimal("1."))
    else:
        discount = Decimal(v.amount).quantize(Decimal("1."))
    discount = min(discount, subtotal)
    return (True, discount, "Áp dụng mã thành công.", v)
