from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Category


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ('slug',)                  # dùng slug làm khóa để update
        fields = ('category_name', 'slug', 'description', 'cat_image')

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_classes = [CategoryResource]
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug')
    list_filter = ('category_name',)
    search_fields = ('category_name', 'slug')
    ordering = ('-id',)
