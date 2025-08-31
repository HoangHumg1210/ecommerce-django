from django.shortcuts import render, redirect
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order


def payments(request):
    return render(request, 'orders/payments.html')

def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    tax = total * 0.02
    grand_total = total + tax

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
            return redirect('checkout')  # Đặt hàng thành công thì redirect
        else:
            # In lỗi ra terminal để debug
            print("Form lỗi:", form.errors)
            # Render lại chính trang đặt hàng để user thấy lỗi
            context = {
                'cart_items': cart_items,
                'total': total,
                'quantity': quantity,
                'tax': tax,
                'grand_total': grand_total,
                'form': form,         # Truyền form lỗi ra template
            }
            return render(request, 'store/checkout.html', context)
    else:
        form = OrderForm()
        context = {
            'cart_items': cart_items,
            'total': total,
            'quantity': quantity,
            'tax': tax,
            'grand_total': grand_total,
            'form': form,
        }
        return render(request, 'store/checkout.html', context)
