from django.db import models
from accounts.models import Account
from store.models import Product, Variation
from django.contrib.auth import get_user_model
User = get_user_model()


class Voucher(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    TYPE_CHOICES = [(PERCENT, 'Percent'), (FIXED, 'Fixed amount')]

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PERCENT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)         # % hoặc số tiền
    min_order_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)      # tổng lượt dùng
    per_user_limit = models.PositiveIntegerField(default=1)               # mỗi user dùng tối đa
    only_first_order = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.code.upper()

class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order_number = models.CharField(max_length=50, blank=True, default="")
    used_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):  
    STATUS = (
        ('COMPLETED', 'Hoàn tất'),
        ('PENDING', 'Đang xử lý'),
        ('FAILED', 'Thất bại'),
        ('CANCELED', 'Đã hủy'),
        ('REFUNDED', 'Đã hoàn tiền'),
        ('COD', 'Thanh toán khi nhận hàng (COD)'),
    )

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=100, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    STATUS = (     
    ('New', 'Mới'),
    ('Accepted', 'Đã xác nhận'),
    ('Completed', 'Đã hoàn thành'),
    ('Cancelled', 'Đã hủy'),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.address_line_1}'

    def __str__(self):
        return self.first_name


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name
    
class OrderProductVariation(models.Model):
    orderproduct = models.ForeignKey(OrderProduct, on_delete=models.CASCADE)
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)

    class Meta:
        db_table = 'orders_orderproduct_variations'
        managed = False
        unique_together = (('orderproduct', 'variation'),)