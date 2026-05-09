from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login,authenticate,logout,get_user_model
from .models import Category,Product,Cart,CartItem,Rating,Order,OrderItem,User
from django.contrib import messages
from .forms import RegistrationForm,RatingForm,CheckOutForm,ProfileUpdateForm
from django.db.models import Q,Max,Min,Avg
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .utils import generate_sslcommerz_payment,send_order_confirmation_email
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
# Create your views here.

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user=authenticate(request,email=email,password=password)

        if user is not None:
            login(request, user)
            return redirect('e_shop:home')
        else:
            messages.error(request, "Invalid email or password")

    return render(request, 'e_shop/login.html')  

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,"Registration successful!")
    else:
        form = RegistrationForm()
    return render(request,'e_shop/register.html',{'form': form})

def logout_view(request):
    logout(request)
    return redirect('e_shop:home')

def home(request):
    featured_products= Product.objects.filter(available=True).order_by('-created')[:8]
    categories = Category.objects.all()

    return render(request,'e_shop/home.html',{
        'featured_products': featured_products,
        'categories':categories
    })

def product_list(request,category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available = True)

    if category_slug:
        category = get_object_or_404(Category,slug=category_slug)
        products = products.filter(category=category)

    min_price = products.aggregate(Min('price'))['price__min']
    max_price = products.aggregate(Max('price'))['price__max']

    if request.GET.get('min_price'):
        products = products.filter(price__gte=request.GET.get('min_price'))
    if request.GET.get('max_price'):
        products = products.filter(price__lte=request.GET.get('max_price'))
    if request.GET.get('rating'):
        min_rating = request.GET.get('rating')
        products = products.annotate(avg_rating=Avg('rating__rating')).filter(avg_rating__gte=min_rating)

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    return render(request,'e_shop/product_list.html',{
        'category' : category,
        'categories' : categories,
        'products' : products,
        'min_price' : min_price,
        'max_price' : max_price
    })


def product_detail(request,slug):
    product = get_object_or_404(Product,slug=slug,available=True)
    related_product = Product.objects.filter(category = product.category).exclude(slug=slug)
    user_rating = None
    ratings = product.ratings.select_related('user').order_by('-created')
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product,user=request.user)
        except Rating.DoesNotExist:
            pass
    rating_form = RatingForm(instance=user_rating)

    return render(request,'e_shop/product_detail.html',{
        'product': product,
        'related_product' : related_product,
        'user_rating': user_rating,
        'ratings':ratings,
        'rating_form': rating_form,
    })

@login_required(login_url='/login/')
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    return render(request,'e_shop/cart.html',{'cart':cart})

@login_required(login_url='/login/')
def cart_add(request,product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        cart = Cart.objects.get(user = request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user = request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart,product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart,product=product,quantity = 1)
        messages.success(request,f"{product.name} has been added to your cart!")

    return redirect('e_shop:product_list')

@login_required(login_url='/login/')
@require_POST
def cart_update(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        quantity = 1

    if quantity > product.stock:
        return JsonResponse({
            'success': False,
            'error': f'Only {product.stock} item(s) in stock. You cannot add more.'
        }, status=400)

    if quantity <= 0:
        cart_item.delete()
        message = f"{product.name} removed from cart"
    else:
        cart_item.quantity = quantity
        cart_item.save()
        message = f"{product.name} quantity updated to {quantity}"

    return JsonResponse({'success': True, 'message': message, 'new_quantity': quantity})


@login_required
@require_POST
def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    cart_item.delete()
    return JsonResponse({'success': True, 'message': f"{product.name} removed"})
@csrf_exempt
@login_required(login_url='/login/')
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, "Your cart is empty!")
            return redirect('e_shop:product_list')
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty!")
        return redirect('e_shop:cart_detail')
    
    initial_data = {}
    if request.user.first_name:
        initial_data['first_name'] = request.user.first_name
    if request.user.last_name:
        initial_data['last_name'] = request.user.last_name
    if request.user.email:
        initial_data['email'] = request.user.email

    if request.method == 'POST':
        form = CheckOutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            cart.items.all().delete()
            request.session['order_id'] = order.id
        return redirect('e_shop:payment_process')
    else:
        form = CheckOutForm(initial=initial_data)

    return render(request, 'e_shop/checkout.html', {
        'cart': cart,
        'form': form
    })
            
@csrf_exempt
@login_required(login_url='/login/')
def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('e_shop:home')
    order = get_object_or_404(Order,id=order_id)
    payment_data = generate_sslcommerz_payment(order, request)

    if payment_data['status'] == 'SUCCESS':
        return redirect(payment_data['GatewayPageURL'])
    else:
        messages.error(request, "Payment Geteway not find. Please Try again.")
        print(payment_data)
        return redirect('e_shop:checkout')
    

@csrf_exempt
@login_required
def payment_success(request,order_id):
    order = get_object_or_404(Order, id=order_id,user=request.user)
    order.paid = True
    order.status = 'processing'
    order.transaction_id = request.POST.get('bank_tran_id',order_id)
    order.save()

    order_items = order.items.all()
    for item in order_items:
        product = item.product
        product.stock -= item.quantity

        if product.stock < 0:
            product.stock = 0
        product.save()
    
    send_order_confirmation_email(order)
    messages.success(request,"Payment Successful!")
    return render(request,'e_shop/payment_success.html')

@csrf_exempt
@login_required
def payment_fail(request,order_id):
    order = get_object_or_404(Order, id= order_id, user=request.user)
    order.status = 'canceled'
    order.save()
    return render(request,'e_shop/checkout.html')

@csrf_exempt
@login_required(login_url='/login/')
def payment_cancel(request,order_id):
    order = get_object_or_404(Order, id= order_id, user=request.user)
    order.status = 'canceled'
    order.save()
    return redirect('e_shop/cart_detail')

@login_required(login_url='/login/')
def profile(request):
    tab = request.GET.get('tab')

    orders = Order.objects.filter(user=request.user).order_by('-created')
    completed_orders = orders.filter(status='delivered').count()
    total_spent = sum(order.get_total_cost() for order in orders if order.paid)

    order_history_active = (tab == 'orders')
    # edit_active = (tab == 'edit')


    return render(request, 'e_shop/profile.html', {
        'user': request.user,
        'orders': orders,
        'order_history_active': order_history_active,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
    })

@login_required(login_url='/login/')
def profile_update(request):

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('e_shop:profile')  # or your profile url name

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'e_shop/profile_update.html', {'form': form})


@login_required(login_url='/login/')
def rate_product(request,product_id):
    product = get_object_or_404(Product, id=product_id)
    ordered_items = OrderItem.objects.filter(
        order__user=request.user,
        order__paid=True,
        product=product
    )

    if not ordered_items.exists():
        messages.warning(request,"You can only rate products you have purched!")
        return redirect('e_shop:product_detail', slug=product.slug)
    try:
        rating = Rating.objects.filter(product=product, user=request.user).first()
    except Rating.DoesNotExist:
        rating = None

    if request.method == 'POST':
        form = RatingForm(request.POST, instance = rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user
            rating.save()
            return redirect('e_shop:product_detail', slug=product.slug)
        
    else:
        form = RatingForm(instance=rating)
    return render(request,'e_shop/rate_product.html',{
        'form': form,
        'product': product
    })