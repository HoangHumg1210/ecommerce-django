from django.db import models
from store.models import Product, Variation
# Create your models here.



class Cart(models.Model):#Cart: Đại diện cho một giỏ hàng (thường gắn với 1 session/user).
    cart_id = models.CharField(max_length=255, unique=True)  #cart_id: khóa phân biệt từng giỏ hàng (thường là session key của user).
    date_added = models.DateTimeField(auto_now_add=True)  #date_added: ngày tạo giỏ hàng. 
    
    
    def __str__(self):
        return self.cart_id
    
class CartItem(models.Model):    #CartItem: Một sản phẩm nằm trong giỏ.
    product = models.ForeignKey(Product, on_delete=models.CASCADE) #product: Tham chiếu đến model Product.
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE) #cart: Tham chiếu về Cart chứa sản phẩm đó.
    quantity = models.IntegerField() #quantity: Số lượng sản phẩm này trong giỏ.
    is_active = models.BooleanField(default=True) #is_active: Cho phép “ẩn” CartItem thay vì xóa cứng.
    
    #sub_total(): Tính tổng tiền của sản phẩm đó (giá * số lượng).
    def sub_total(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return self.product.product_name
    


    