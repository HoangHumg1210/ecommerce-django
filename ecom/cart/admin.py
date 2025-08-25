from django.contrib import admin
from .models import Cart, CartItem

# Register your models here.

class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')
    
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'is_active')

    def list_variations(self, obj):
        return ", ".join(
            [f"{v.variation_category}: {v.variation_value}" for v in obj.variations.all()]
        )
    list_variations.short_description = 'Variations'
    
    
admin.site.register(Cart)
admin.site.register(CartItem, CartItemAdmin)