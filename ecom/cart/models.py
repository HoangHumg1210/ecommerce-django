from django.db import models
from store.models import Product, Variation
from accounts.models import Account


class Cart(models.Model):
    """Cart: Đại diện cho một giỏ hàng (thường gắn với 1 session/user)."""
    cart_id = models.CharField(max_length=255, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    """CartItem: Một sản phẩm nằm trong giỏ."""
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    # chỉ giữ 1 ManyToManyField, dùng through để liên kết biến thể
    variations = models.ManyToManyField(
        Variation,
        through='CartItemVariation',
        blank=True,
        related_name='cart_items'
    )

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.product_name


class CartItemVariation(models.Model):
    cartitem = models.ForeignKey(CartItem, on_delete=models.CASCADE)
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)

    class Meta:
        db_table = 'cart_cartitem_variations'
        # ❗ Nếu bảng chưa có trong DB, bỏ dòng này để Django tự tạo
        managed = False
        unique_together = (('cartitem', 'variation'),)

    def __str__(self):
        return f"{self.cartitem.product.product_name} - {self.variation.variation_category}: {self.variation.variation_value}"
