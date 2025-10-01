from django.db import models
from django.urls import reverse
from category.models import Category
from accounts.models import Account
from django.db.models import Avg, Count


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

    material = models.CharField(max_length=200, blank=True, null=True)
    form = models.CharField(max_length=200, blank=True, null=True)

    def full_description(self):
        desc = f"<h5>{self.product_name}</h5>"
        if self.material:
            desc += f"<p><b>Chất liệu:</b> {self.material}</p>"
        if self.form:
            desc += f"<p><b>Form:</b> {self.form}</p>"

        if self.description:
            parts = [p.strip() for p in self.description.split("\n") if p.strip()]
            if parts:
                desc += "<ul class='product-bullets'>"
                for p in parts:
                    desc += f"<li>{p}</li>"
                desc += "</ul>"

        return desc
    
    
    def get_url(self):
        return reverse('products_by_detail', args=[self.category.slug, self.slug])
    
    def __str__(self):
        return self.product_name

    def averageReview(self):
        data = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        return float(data['average']) if data['average'] is not None else 0.0

    def countReview(self):
        data = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        return int(data['count']) if data['count'] is not None else 0


class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)
    
    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)
         



variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)
class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return f"{self.variation_category}: {self.variation_value}"

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

class ProductGallery(models.Model):
    product = models.ForeignKey(Product,default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'product_gallery'
        verbose_name_plural = 'product_gallery'