from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from orders.models import Order
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from cart.models import Cart, CartItem  
from cart.views import _cart_id  
import requests

# Create your views here.

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                username=username,
                password=password)
            
            user.phone_number = phone_number
            user.save()

            # User Activation
            current_site = get_current_site(request)
            mail_subject = 'Vui lòng kích hoạt tài khoản của bạn'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),

            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Cảm ơn bạn đã đăng ký! Chúng tôi đã gửi email xác nhận tới địa chỉ email của bạn. Vui lòng kiểm tra hộp thư và xác nhận tài khoản.')
            # return redirect('register')
            return redirect('/accounts/login/?command=verification&email=' + email)
            
        context = {'form': form}
        return render(request, 'accounts/register.html', context)
    else:
        form = RegistrationForm()
        context = {'form': form}
        return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']


        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                
                if is_cart_item_exists: 
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    for item in cart_item:
                        item.user = user
                        item.save()
            except:
                pass
            
            
            auth.login(request, user)
            messages.success(request, 'Đăng nhập thành công!' )
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
               
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)

            except:
                return redirect('dashboard')
                
            
        else:
            messages.error(request, "Tài khoản hoặc mật khẩu không chính xác")
            return redirect('login')
    return render(request, 'accounts/login.html')


@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    # messages.success("Đăng xuất")
    return redirect('login')


def activate(request, uidb64, token ):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Tài khoản của bạn đã được kích hoạt thành công. Vui lòng đăng nhập để tiếp tục')
        return redirect('login')
    else:
        messages.error(request, 'Liên kết xác thực không hợp lệ')
        return redirect('register')


@login_required(login_url='login')        
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    context = {
        'orders_count': orders_count,
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = Account.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = 'Nhập lại mật khẩu'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Email đặt lại mật khẩu đã được gửi tới địa chỉ email của bạn')
            return redirect('login')
        except Account.DoesNotExist:
            messages.error(request, 'Tài khoản không tồn tại')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')



def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Vui lòng nhập mật khẩu mới')
        return redirect('resetPassword')
    else:
        messages.error(request, 'Liên kết này đã hết hạn hoặc không hợp lệ! ')
        return redirect('login')
        
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if  password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Mật khẩu của bạn được thay đổi thành công')
            return redirect('login')
        else:
            messages.error(request, 'Mật khẩu nhập lại không khớp. Vui lòng thử lại.')
            return redirect('resetPassword')
    else:        
        return render(request, 'accounts/resetPassword.html')

def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }

    return render(request, 'accounts/my_orders.html', context)

def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Cập nhật thành công')
            return redirect('edit_profile')
        else:
            user_form = UserForm(instance=request.user)
            profile_form = UserProfileForm(instance=request.user.profile)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }

    return render(request, 'accounts/edit_profile.html')