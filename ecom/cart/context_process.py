from .models import Cart, CartItem
from django.conf import settings
from .views import _cart_id


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.filter(cart=cart)
            for cart_item in cart_item:
                cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
            
    return dict(cart_count=cart_count)

                