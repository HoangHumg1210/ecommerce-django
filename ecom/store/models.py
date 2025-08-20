from django.db import models

from category.models import Category
# Create your models here.
class Product(models.Model):
    product_name     = models.CharField(max_length=200, unique=True)
    slug             = models.SlugField(max_length=200, unique= True)
    description      = models.TextField(max_length=500, blank=True)
    price            = models.IntegerField()
    image            = models.ImageField(upload_to='photos/products')
    stock            = models.IntegerField() # sản lượng tồn kho
    is_available     = models.BooleanField(default=True)  # có sẵn hay ko
    category         = models.ForeignKey(Category, on_delete=models.CASCADE) # nếu danh mục bị xóa thì sản phẩm cũng sẽ bị xóa
    created_date     = models.DateTimeField(auto_now_add=True)     # ngày tạo
    modified_date    = models.DateTimeField(auto_now=True) # ngày sửa đổi
    
    
    def __str__(self):
        return self.product_name