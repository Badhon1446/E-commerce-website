from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=100,unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True,null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100,unique= True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categoris'

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200,unique=True)
    category= models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.PositiveBigIntegerField(default=1)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d')

    def __str__(self):
        return self.name
    
    def average_rating(self):
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
        return 0
    
class Rating(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"
    
class Cart(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for{self.user.username}"
    def get_total_price(self):
        return sum(item.get_cost() for item in self.item.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name="items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} X {self.product.name}"
    def get_cost(self):
        return self.product.price*self.quantity
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=5)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=10,choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"Order #{self.id}"
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10,decimal_places=2)


    def __str__(self):
        return f"{self.quantity} X {self.product.name}"
    def get_cost(self):
        return self.price*self.quantity
