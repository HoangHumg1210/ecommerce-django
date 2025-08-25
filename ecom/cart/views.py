from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart
    
# def add_cart(request, product_id):
#     product = Product.objects.get(id=product_id)
#     product_variation = []
#     if request.method == 'POST':
#         for item in request.POST:
#             key = item
#             value = request.POST[key]
#             try:
#                 variation = Variation.objects.get(
#                     product=product, 
#                     variation_category__iexact=key, 
#                     variation_value__iexact=value
#                 )
#                 product_variation.append(variation)
#             except Variation.DoesNotExist:
#                 pass

#     try:
#         cart = Cart.objects.get(cart_id=_cart_id(request))
#     except Cart.DoesNotExist:
#         cart = Cart.objects.create(cart_id=_cart_id(request))
#     cart.save()
    
#     is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
#     if is_cart_item_exists:
#         cart_item = CartItem.objects.filter( product=product, cart=cart)
#         # existing_variations -> database
#         # current variation -> product_variation
#         # item_id -> database

#         ex_var_list = []
#         id = []

#         for item in cart_item:
#             exitsting_variation = item.variations.all() 
#             ex_var_list.append(list(exitsting_variation))
#             id.append(item.id)


#         if product_variation in ex_var_list:
#             # increase the cart item quatity
#             index = ex_var_list.index(product_variation)
#             item_id = id[index]
#             item = CartItem.objects.get(product=product, id=item_id)
#             item.quantity += 1
#             item.save() 
#         else:
#             # create a new cart item
#             item = CartItem.objects.create(product=product, quantity = 1, cart = cart)
#             if len(product_variation) > 0:
#                 item.variations.clear()
#                 item.variations.add(*product_variation)
#             item.save()
#     else:
#         cart_item = CartItem.objects.create(
#             product = product,
#             quantity = 1,
#             cart = cart,
#         )
#         if len(product_variation) > 0:
#             cart_item.variations.clear()
#             cart_item.variations.add(*product_variation)
#         cart_item.save()
#     return redirect('cart')
        
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
    cart_items = CartItem.objects.filter(product=product, cart=cart)
    found = False

    input_var_set = set()
    for v in product_variation:
        tup = (v.variation_category, v.variation_value)
        input_var_set.add(tup)

    for item in cart_items:
        item_var_set = set()
        for v in item.variations.all():
            tup = (v.variation_category, v.variation_value)
            item_var_set.add(tup)
        if input_var_set == item_var_set:
            item.quantity += 1
            item.save()
            found = True
            break

    if not found:
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


    
# def remove_cart_item(request, product_id):
#     cart = Cart.objects.get(cart_id=_cart_id(request))
#     product_id = get_object_or_404(Product, id=product_id)
#     cart_item = CartItem.objects.get(product=product_id, cart=cart)
#     cart_item.delete()
#     return redirect('cart')
def remove_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

    
    
# def cart(request, total=0, quantity=0, cart_items=None):
#     try:
#         tax = 0
#         grand_total = 0
#         cart = Cart.objects.get(cart_id=_cart_id(request))
#         cart_items = CartItem.objects.filter(cart=cart, is_active=True)
#         for cart_item in cart_items:
#             total += (cart_item.product.price * cart_item.quantity)
#             quantity += cart_item.quantity
#         tax = (total * 0.02)  
#         grand_total = total + tax 

#     except Cart.ObjectDoesNotExist:
#         pass 
    
#     context ={
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'tax': tax,
#         'grand_total': grand_total,
#     }
#     return render(request, 'store/cart.html', context)

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (total * 0.02)  
        grand_total = total + tax 

    except Cart.ObjectDoesNotExist:
        pass 
    
    context ={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


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
