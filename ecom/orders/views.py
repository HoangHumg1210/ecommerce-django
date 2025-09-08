from django.shortcuts import render, redirect
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
from .models import OrderProduct, Product, Order, Payment
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import JsonResponse
import json

def payments(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

            payment = Payment.objects.create(
                user=request.user,
                payment_id=body['transactionID'],  
                payment_method=body['payment_method'],
                amount_paid=order.order_total,
                status=body['status'],
            )

            order.payment = payment
            order.is_ordered = True
            order.save()

            cart_items = CartItem.objects.filter(user=request.user)
            for item in cart_items:
                orderproduct = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True,
                )
                # Gán variations đúng cách
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variations.all()
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.variations.set(product_variation)
                orderproduct.save()
            
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()
            CartItem.objects.filter(user=request.user).delete()
            # print('Xóa thành công!')
            order_time = timezone.localtime(order.created_at)
            order_products = order.orderproduct_set.all()  # Lấy toàn bộ sản phẩm đã đặt
            mail_subject = 'Cảm ơn bạn đã đặt hàng'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
                'shop_name': 'Double H Store',
                'order_time': order_time,
                'order_products': order_products,    
                'year': order_time.year,            
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = "html"
            send_email.send()
            
            
            return JsonResponse({'status': 'success', 'message': 'Payment completed!'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request.'})


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
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
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
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
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
        
