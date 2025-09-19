from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .utils import check_voucher
from django.contrib import messages
# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    # LẤY SỐ LƯỢNG NGƯỜI DÙNG CHỌN (mặc định 1)
    qty = 1
    if request.method == 'POST':
        # quantity có thể là input type="number" hoặc hidden
        qty = int(request.POST.get('quantity', 1))

        # gom variations
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
    cart.save()

    # lọc cart_items theo user hoặc cart
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    # so khớp biến thể
    input_var_set = set((v.variation_category, v.variation_value) for v in product_variation)
    for item in cart_items:
        item_var_set = set((v.variation_category, v.variation_value) for v in item.variations.all())
        if input_var_set == item_var_set:
            item.quantity += qty           # <<< CỘNG THEO SỐ LƯỢNG CHỌN
            item.save()
            break
    else:
        # chưa có item trùng biến thể -> tạo mới với đúng qty
        params = dict(product=product, quantity=qty, cart=cart)
        if request.user.is_authenticated:
            params['user'] = request.user
        cart_item = CartItem.objects.create(**params)
        if product_variation:
            cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect('cart')




def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product_id = get_object_or_404(Product, id=product_id)
    try: 
        cart_item = CartItem.objects.get(product=product_id, cart= cart)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        return HttpResponse("Không có sản phẩm trong giỏ hàng")
    
    return redirect('cart')

def remove_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

 
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('id')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (total * 0.02)
        grand_total = total + tax
    except Cart.DoesNotExist:
        cart_items = []
        tax = 0
        grand_total = 0
        total = 0
        quantity = 0

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        # chỉ cho phép checkout khi đăng nhập => lấy cart_items theo user
        cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('id')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (total * 0.02)  
        grand_total = total + tax 
    except Exception:
        cart_items = []
        tax = 0
        grand_total = 0
        total = 0
        quantity = 0

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)


def increase_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

def decrease_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def apply_voucher(request):
    if request.method == "POST":
        code = request.POST.get("voucher_code", "")
        subtotal = Decimal(request.POST.get("subtotal", "0"))
        ok, discount, msg, v = check_voucher(request, subtotal, code)
        if ok:
            request.session["voucher_code"] = v.code
            request.session["voucher_discount"] = float(discount)
            messages.success(request, msg)
        else:
            request.session.pop("voucher_code", None)
            request.session.pop("voucher_discount", None)
            messages.warning(request, msg)
    return redirect(request.POST.get("next") or "cart")

def remove_voucher(request):
    request.session.pop("voucher_code", None)
    request.session.pop("voucher_discount", None)
    messages.info(request, "Đã bỏ mã giảm giá.")
    return redirect(request.GET.get("next") or "cart")