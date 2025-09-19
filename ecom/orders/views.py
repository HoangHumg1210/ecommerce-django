from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
import re
import json
from django.http import JsonResponse
from .models import OrderProduct, Product, Order, Payment
from store.models import Product


from django.http import JsonResponse
import json

from django.shortcuts import render, redirect
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
import re
import json
from django.http import JsonResponse
from .models import OrderProduct, Order, Payment
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import JsonResponse
import json

def payments(request):
    if request.method != "POST":
        return JsonResponse({'status': 'fail', 'message': 'Invalid request.'}, status=400)

    try:
        body = json.loads(request.body)

        # DÙNG MÃ ĐƠN NỘI BỘ, KHÔNG DÙNG orderID CỦA PAYPAL
        order_no = body.get('local_order_number')
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_no)

        # payment_id: ưu tiên transactionID; nếu trống (COD) thì tạo UUID
        tx_id = body.get('transactionID')
        if not tx_id:
            import uuid
            tx_id = str(uuid.uuid4())

        payment = Payment.objects.create(
            user=request.user,
            payment_id=tx_id,
            payment_method=body.get('payment_method') or 'COD',
            amount_paid=body.get('amount') or order.order_total,
            status=body.get('status') or 'COD',
        )

        # Chốt đơn
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Chuyển CartItem -> OrderProduct
        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            op = OrderProduct.objects.create(
                order=order, payment=payment, user=request.user,
                product=item.product, quantity=item.quantity,
                product_price=item.product.price, ordered=True,
            )
            op.variations.set(item.variations.all())
            op.save()

            # Trừ tồn
            p = item.product
            p.stock = max(0, p.stock - item.quantity)
            p.save()

        cart_items.delete()

        return JsonResponse({'order_number': order.order_number, 'payment_id': payment.payment_id})

    except Order.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Order not found (wrong local_order_number or already ordered).'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)



def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    usd_rate = 26389
    tax = total * 0.02
    grand_total = total + tax
    grand_total_usd = round(grand_total / usd_rate, 2)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Tạo order_number duy nhất
            today = datetime.date.today()
            current_date = today.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
               'order': order,
               'cart_items': cart_items,
               'total': total,
               'tax': tax,
               'grand_total': grand_total,
               'grand_total_usd': grand_total_usd,
            }
            return render(request, 'orders/payments.html', context)
        else:

            return render('checkout')






from django.shortcuts import render, redirect, get_object_or_404

def order_complete(request):
    order_number = request.GET.get('order_number')
    if not order_number:
        return redirect('home')


    order = get_object_or_404(Order, order_number=order_number, is_ordered=True)


    ordered_products = OrderProduct.objects.filter(order=order).select_related('product')


    subtotal = sum(op.product_price * op.quantity for op in ordered_products)


    payment = order.payment
    if not payment:
        return redirect('home')

    context = {
        'order': order,
        'ordered_products': ordered_products,
        'order_number': order.order_number,
        'transID': payment.payment_id,
        'subtotal': subtotal,
    }
    return render(request, 'orders/order_complete.html', context)





