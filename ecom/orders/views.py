from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import re
import json
from django.http import JsonResponse
from .models import OrderProduct, Product, Order, Payment
from store.models import Product
from django.http import HttpResponse
from .forms import OrderForm
import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
import uuid
from decimal import Decimal


# ---------------------- PAYMENTS ----------------------
from django.db import transaction

@transaction.atomic
def payments(request):
    if request.method != "POST":
        return JsonResponse({'status': 'fail', 'message': 'Invalid request.'}, status=400)
    try:
        body = json.loads(request.body or "{}")
        order_no = body.get('local_order_number')
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_no)


        disc = Decimal(str(request.session.get('voucher_discount', 0)))  # vd 15000
        if disc < 0:
            disc = Decimal('0')

        # 2) Tính payable dựa trên tổng cũ của order (đã gồm thuế)
        #    Nếu muốn chặt chẽ hơn, có thể tự cộng lại từ CartItem.
        payable = Decimal(order.order_total) - disc
        if payable < 0:
            payable = Decimal('0')

        # 3) Tạo Payment
        tx_id = body.get('transactionID') or str(uuid.uuid4())
        payment_method = body.get('payment_method') or 'COD'
        status = body.get('status') or ('COD' if payment_method == 'COD' else 'Completed')
        payment = Payment.objects.create(
            user=request.user,
            payment_id=tx_id,
            payment_method=payment_method,
            amount_paid=payable,
            status=status,
        )

        order.payment = payment
        order.order_total = payable
        if hasattr(order, "voucher_code"):
            order.voucher_code = (
                request.session.get('voucher_code', '') or
                request.session.get('voucher_codes', '')
            )
        order.is_ordered = True
        order.save()


        cart_items = CartItem.objects.filter(user=request.user).select_related('product').prefetch_related('variations')
        for item in cart_items:
            op = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,  # giá tại thời điểm đặt
            )
            try:
                op.variations.set(item.variations.all())
            except Exception:
                pass
            if hasattr(item.product, 'stock'):
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save()
        cart_items.delete()


        for k in ("voucher_code", "voucher_codes", "voucher_discount"):
            request.session.pop(k, None)

        try:
            ordered_products = OrderProduct.objects.filter(
                order=order
            ).select_related('product').prefetch_related('variations')

            # Tính lại subtotal & discount giống order_complete
            subtotal = sum(Decimal(op.product_price) * op.quantity for op in ordered_products)
            discount = (subtotal + Decimal(order.tax)) - Decimal(order.order_total)
            if discount < 0:
                discount = Decimal('0')

            mail_subject = f"H2H Store – Hóa đơn #{order.order_number}"
            html_message = render_to_string('orders/email_invoice.html', {
                'order': order,
                'ordered_products': ordered_products,
                'subtotal': subtotal,
                'discount': discount,
            })
            to_email = request.user.email
            email = EmailMessage(mail_subject, html_message, to=[to_email])
            email.content_subtype = "html"  # gửi HTML
            email.send(fail_silently=True)
        except Exception:
            # Không chặn thanh toán nếu gửi mail lỗi
            pass

        return JsonResponse({'order_number': order.order_number, 'payment_id': payment.payment_id})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'fail', 'message': 'Order not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)


# ---------------------- PLACE ORDER ----------------------
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    if not cart_items.exists():
        return redirect('store')

    # Tính tổng
    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    usd_rate = 26389
    tax = total * 0.02

    # KHÔNG xoá session voucher ở đây để người dùng vẫn thấy giảm giá khi tới trang payments
    discount = Decimal("0")
    payable = Decimal(total) + Decimal(tax)
    grand_total_usd = round(payable / usd_rate, 2)

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
            data.order_total = payable
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # order_number duy nhất
            today = datetime.date.today().strftime('%Y%m%d')
            order_number = today + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'discount': discount,
                'voucher_code': request.session.get("voucher_code") or request.session.get("voucher_codes"),
                'grand_total': payable,
                'grand_total_usd': grand_total_usd,
            }
            return render(request, 'orders/payments.html', context)

        return redirect('checkout')


# ---------------------- ORDER COMPLETE ----------------------
def order_complete(request):
    on = request.GET.get('order_number')
    if not on:
        return redirect('home')

    order = get_object_or_404(Order, order_number=on, is_ordered=True)
    ordered_products = OrderProduct.objects.filter(order=order).select_related('product')

    # subtotal = sum(price * qty)
    subtotal = sum(Decimal(op.product_price) * op.quantity for op in ordered_products)

    # discount = subtotal + tax - order_total  (không âm)
    discount = (subtotal + Decimal(order.tax)) - Decimal(order.order_total)
    if discount < 0:
        discount = Decimal('0')

    context = {
        'order': order,
        'ordered_products': ordered_products,
        'order_number': order.order_number,
        'transID': order.payment.payment_id if order.payment else '',
        'subtotal': subtotal,
        'discount': discount,
        # Nếu có lưu mã vào order.voucher_code thì hiển thị, còn không vẫn OK
        'voucher_codes': getattr(order, 'voucher_code', ''),
    }
    return render(request, 'orders/order_complete.html', context)