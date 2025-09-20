from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Cart, CartItem
from .utils import check_voucher
from store.models import Product, Variation
import json

# ===== Helpers =====
def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id


# ===== Cart CRUD =====
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    qty = 1
    if request.method == "POST":
        qty = int(request.POST.get("quantity", 1))
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value,
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    input_var_set = {(v.variation_category, v.variation_value) for v in product_variation}
    for item in cart_items:
        item_var_set = {(v.variation_category, v.variation_value) for v in item.variations.all()}
        if input_var_set == item_var_set:
            item.quantity += qty
            item.save()
            break
    else:
        params = dict(product=product, quantity=qty, cart=cart)
        if request.user.is_authenticated:
            params["user"] = request.user
        cart_item = CartItem.objects.create(**params)
        if product_variation:
            cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect("cart")


def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        return HttpResponse("Không có sản phẩm trong giỏ hàng")
    return redirect("cart")


def remove_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def increase_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect("cart")


def decrease_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect("cart")


# ===== Views =====
def cart(request, total=Decimal("0"), quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = (
                CartItem.objects.filter(user=request.user, is_active=True)
                .select_related("product").order_by("id")
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = (
                CartItem.objects.filter(cart=cart, is_active=True)
                .select_related("product").order_by("id")
            )

        for ci in cart_items:
            total += Decimal(str(ci.product.price)) * ci.quantity
            quantity += ci.quantity

        tax = total * Decimal("0.02")
        grand_total = total + tax

        discount = Decimal(str(request.session.get("voucher_discount", 0)))
        payable = grand_total - discount
        if payable < 0:
            payable = Decimal("0")

    except Cart.DoesNotExist:
        cart_items = []
        tax = grand_total = total = Decimal("0")
        quantity = 0
        discount = payable = Decimal("0")

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
        "discount": discount,
        "payable": payable,
        "voucher_code": request.session.get("voucher_code"),
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request, total=Decimal("0"), quantity=0, cart_items=None):
    try:
        cart_items = (
            CartItem.objects.filter(user=request.user, is_active=True)
            .select_related("product").order_by("id")
        )
        for ci in cart_items:
            total += Decimal(str(ci.product.price)) * ci.quantity
            quantity += ci.quantity

        tax = total * Decimal("0.02")
        grand_total = total + tax

        discount = Decimal(str(request.session.get("voucher_discount", 0)))
        payable = grand_total - discount
        if payable < 0:
            payable = Decimal("0")

    except Exception:
        cart_items = []
        tax = grand_total = total = Decimal("0")
        quantity = 0
        discount = payable = Decimal("0")

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
        "discount": discount,
        "payable": payable,
        "voucher_code": request.session.get("voucher_code"),
    }
    return render(request, "store/checkout.html", context)


@require_POST
def apply_voucher(request):
    is_json = request.content_type == "application/json"

    # --- lấy input ---
    if is_json:
        import json
        from decimal import Decimal
        payload = json.loads(request.body or "{}")
        raw_codes = payload.get("codes") or [payload.get("code", "")]
        if isinstance(raw_codes, str):
            raw_codes = [raw_codes]
        subtotal = Decimal(str(payload.get("subtotal", "0")))
    else:
        from decimal import Decimal
        raw_codes = [request.POST.get("voucher_code", "")]
        subtotal = Decimal(str(request.POST.get("subtotal", "0") or "0"))

    # ====== GỘP MÃ: ưu tiên mã vừa nhập, loại trùng (case-insensitive), tối đa 2 ======
    # Codes đang có trong session (nếu trước đó đã áp)
    existed = [str(c).strip().upper() for c in request.session.get("voucher_codes", []) if c]
    # Codes mới nhập
    incoming = [str(c).strip().upper() for c in raw_codes if c and str(c).strip()]

    # Nếu nhập >= 2 mã trong 1 lần: coi như "đặt lại" danh sách
    base = [] if len(incoming) >= 2 else existed
    merged = base + incoming  # ưu tiên phần đuôi (mã mới)

    # Loại trùng (không phân biệt hoa/thường) nhưng giữ thứ tự ưu tiên mã mới
    seen, dedup_rev = set(), []
    for c in reversed(merged):
        k = c.lower()
        if k not in seen:
            seen.add(k)
            dedup_rev.append(c)
    codes = list(reversed(dedup_rev))[:2]
    # ================================================================================

    if not codes:
        return JsonResponse({"ok": False, "message": "Chưa nhập mã."}, status=400)

    # --- kiểm tra từng mã ---
    applied, total_discount, errs = [], Decimal("0"), []
    for c in codes:
        ok, disc, msg, v = check_voucher(request, subtotal, c)
        if ok:
            applied.append(v.code.upper())
            total_discount += Decimal(str(disc))
        else:
            errs.append(f"{c}: {msg}")

    if not applied:
        return JsonResponse({"ok": False, "message": " ; ".join(errs) or "Mã không hợp lệ."}, status=400)

    if total_discount > subtotal:
        total_discount = subtotal

    # Lưu session
    request.session["voucher_codes"] = applied               # ví dụ ['T10','T20']
    request.session["voucher_code"]  = " + ".join(applied)   # "T10 + T20"
    request.session["voucher_discount"] = float(total_discount)

    return JsonResponse({
        "ok": True,
        "discount": int(total_discount),
        "applied_codes": applied,
        "message": f"Đã áp dụng: {', '.join(applied)}"
    })


@require_POST
def remove_voucher(request):
    for k in ("voucher_code", "voucher_codes", "voucher_discount"):
        request.session.pop(k, None)
    if request.content_type == "application/json":
        return JsonResponse({"ok": True, "message": "Đã bỏ mã giảm giá."})
    messages.info(request, "Đã bỏ mã giảm giá.")
    return redirect(request.GET.get("next") or "cart")
