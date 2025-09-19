from django.contrib import admin
from .models import Payment, Order, OrderProduct
from .models import Voucher, VoucherRedemption

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'phone', 'city', 'order_total','tax', 'status', 'is_ordered', 'created_at' ]
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone']
    list_per_page = 20
    inlines = [OrderProductInline]


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("code","discount_type","amount","min_order_total","start_at","end_at","is_active")
    list_filter = ("is_active","discount_type")
    search_fields = ("code",)

@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = ("voucher","user","order_number","used_at")

admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
