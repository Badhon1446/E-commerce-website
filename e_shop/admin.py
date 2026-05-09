from django.contrib import admin
from .models import User,Category,Product,Rating,Cart,CartItem,Order,OrderItem
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
#admin.site.register(Category)
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ('username','email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')

    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug':('name',)}


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ['user','rating','comment','created']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name','slug','price','stock','available','created','updated']
    list_filter = ['available','created','updated','category']
    list_editable = ['price','stock','available']
    prepopulated_fields = {'slug':('name',)}
    inlines = [RatingInline]
    

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user','created_at','updated_at']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user','first_name','last_name','email','paid','created','status']
    list_filter = ['paid','created','status']
    inlines = [OrderItemInline]

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user','product','rating','created']
    list_filter = ['rating','created']
