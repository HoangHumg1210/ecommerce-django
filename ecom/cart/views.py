from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cart, CartItem
from .utils import check_voucher
from store.models import Product, Variation


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

    # số lượng mặc định 1
    qty = 1
    if request.method == "POST":
        qty = int(request.POST.get("quantity", 1))

        # gom variations từ form
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

    # lọc item theo user/cart
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    # so khớp biến thể
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
                .select_related("product")
                .order_by("id")
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = (
                CartItem.objects.filter(cart=cart, is_active=True)
                .select_related("product")
                .order_by("id")
            )

        for ci in cart_items:
            # product.price là FloatField -> chuyển sang Decimal bằng str để tránh sai số
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
            .select_related("product")
            .order_by("id")
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


# ===== Voucher =====
def apply_voucher(request):
    if request.method == "POST":
        code = (request.POST.get("voucher_code") or "").strip()
        try:
            subtotal = Decimal(str(request.POST.get("subtotal", "0")))
        except Exception:
            subtotal = Decimal("0")

        ok, discount, msg, v = check_voucher(request, subtotal, code)
        if ok:
            request.session["voucher_code"] = v.code
            request.session["voucher_discount"] = float(discount)  # lưu float để tránh JSON serialize Decimal
            messages.success(request, msg)
        else:
            request.session.pop("voucher_code", None)
            request.session.pop("voucher_discount", None)
            messages.warning(request, msg)

        return redirect(request.POST.get("next") or "cart")
    return redirect("cart")


def remove_voucher(request):
    request.session.pop("voucher_code", None)
    request.session.pop("voucher_discount", None)
    messages.info(request, "Đã bỏ mã giảm giá.")
    return redirect(request.GET.get("next") or "cart")
