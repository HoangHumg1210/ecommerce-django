from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product, 
                    variation_category__iexact=key, 
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
    cart.save()

    # Nếu user đã login thì gắn cả user, nếu chưa thì chỉ gắn cart
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    found = False
    input_var_set = set((v.variation_category, v.variation_value) for v in product_variation)

    for item in cart_items:
        item_var_set = set((v.variation_category, v.variation_value) for v in item.variations.all())
        if input_var_set == item_var_set:
            item.quantity += 1
            item.save()
            found = True
            break

    if not found:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart, user=request.user)
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
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