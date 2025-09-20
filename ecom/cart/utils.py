
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from orders.models import Voucher, VoucherRedemption

def _norm(code: str) -> str:
    return (code or "").strip().upper()

def _q(x: Decimal) -> Decimal:
    # làm tròn tiền (0 chữ số sau dấu phẩy) – đổi nếu bạn muốn 100, 1000 …
    return x.quantize(Decimal("1."), rounding=ROUND_HALF_UP)


def check_voucher(request, subtotal: Decimal, code: str):
    code = (code or "").strip()
    if not code:
        return False, Decimal("0"), "Bạn chưa nhập mã.", None

    try:
        v = (Voucher.objects
           .filter(code__iexact=code, is_active=True)
           .order_by('-id')  # hoặc '-start_at' nếu bạn muốn ưu tiên theo ngày bắt đầu
           .first())
    except Voucher.DoesNotExist:
        return False, Decimal("0"), "Mã không tồn tại hoặc đã ngừng hoạt động.", None

    now = timezone.now()

    # start/end để trống -> bỏ qua kiểm tra thời gian
    if v.start_at and now < v.start_at:
        return False, Decimal("0"), "Mã chưa đến thời gian sử dụng.", v
    if v.end_at and now > v.end_at:
        return False, Decimal("0"), "Mã đã hết hạn.", v

    if subtotal < (v.min_order_total or Decimal("0")):
        return False, Decimal("0"), f"Đơn tối thiểu phải từ {int(v.min_order_total):,}đ.", v

    # limit toàn hệ thống
    if v.usage_limit is not None:
        used_total = VoucherRedemption.objects.filter(voucher=v).count()
        if used_total >= v.usage_limit:
            return False, Decimal("0"), "Mã đã hết lượt sử dụng.", v

    # limit theo user (nếu có đăng nhập)
    if request.user.is_authenticated and v.per_user_limit:
        used_by_user = VoucherRedemption.objects.filter(voucher=v, user=request.user).count()
        if used_by_user >= v.per_user_limit:
            return False, Decimal("0"), "Bạn đã dùng mã này tối đa số lần cho phép.", v

    # tính tiền giảm theo subtotal (trước thuế)
    if v.discount_type == "fixed":
        discount = min(Decimal(v.amount), subtotal)
    else:  # percent
        discount = (subtotal * Decimal(v.amount) / Decimal("100"))
    discount = _q(discount)

    if discount <= 0:
        return False, Decimal("0"), "Mã không mang lại giảm giá hợp lệ.", v

    return True, discount, f"Áp dụng {v.code.upper()} thành công: -{int(discount):,}đ.", v