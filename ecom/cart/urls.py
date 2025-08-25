from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'), # Trang xem giỏ hàng
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'), # Thêm sản phẩm vào giỏ hàng
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'), # Giảm số lượng sản phẩm trong giỏ hàng
    # path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'), # Xóa sản phẩm khỏi giỏ hàng
    path('remove_cart_item/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),




    path('increase_cart_item/<int:cart_item_id>/', views.increase_cart_item, name='increase_cart_item'),
    path('decrease_cart_item/<int:cart_item_id>/', views.decrease_cart_item, name='decrease_cart_item'),


]