import json

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CartAddProductForm, OrderCreateForm, RegisterForm, ReviewForm
from .models import Category, Order, OrderItem, Product, Review
from .payments import create_checkout_session, mark_order_paid_from_session, StripeNotConfigured


def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(available=True)[:11]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query or '',
    })


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    reviews = product.reviews.select_related('user').all()

    recommended_products = (
        Product.objects.filter(category=product.category, available=True)
        .exclude(id=product.id)
        .order_by('-created_at')[:4]
    )
    if recommended_products.count() < 4:
        extra_needed = 4 - recommended_products.count()
        exclude_ids = [product.id] + [p.id for p in recommended_products]
        extra = Product.objects.filter(available=True).exclude(id__in=exclude_ids)[:extra_needed]
        recommended_products = list(recommended_products) + list(extra)

    user_review = None
    review_form = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        if request.method == 'POST':
            review_form = ReviewForm(request.POST, instance=user_review)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, 'Thanks — your review has been posted.')
                return redirect(product.get_absolute_url())
        else:
            review_form = ReviewForm(instance=user_review)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_product_form': cart_product_form,
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
        'recommended_products': recommended_products,
    })


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], size=cd['size'], update_quantity=cd['update'])
        messages.success(request, f'"{product.name}" was added to your cart.')
    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get('size', '')
    cart.remove(product, size=size)
    messages.info(request, f'"{product.name}" was removed from your cart.')
    return redirect('store:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    recommended_products = []
    if len(cart) > 0:
        category_ids = {item['product'].category_id for item in cart}
        cart_product_ids = [item['product'].id for item in cart]
        recommended_products = Product.objects.filter(
            category_id__in=category_ids, available=True
        ).exclude(id__in=cart_product_ids)[:4]
    return render(request, 'store/cart.html', {
        'cart': cart,
        'recommended_products': recommended_products,
    })


def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty. Add some products before checking out.')
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                    size=item['size'],
                )
            cart.clear()

            if order.payment_method == 'card':
                return redirect('store:payment_checkout', order_id=order.id)

            return render(request, 'store/order_success.html', {'order': order})
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {'full_name': request.user.get_full_name() or request.user.username,
                       'email': request.user.email}
        form = OrderCreateForm(initial=initial)

    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})


def payment_checkout(request, order_id):
    """Create a Stripe Checkout Session for the order and redirect the shopper to Stripe."""
    order = get_object_or_404(Order, id=order_id)
    if order.paid:
        return render(request, 'store/order_success.html', {'order': order})

    try:
        session = create_checkout_session(request, order)
    except StripeNotConfigured as exc:
        return render(request, 'store/payment_error.html', {'order': order, 'error': str(exc)})
    except stripe.error.StripeError as exc:
        return render(request, 'store/payment_error.html', {'order': order, 'error': str(exc)})

    return redirect(session.url, permanent=False)


def payment_success(request):
    """Stripe redirects the shopper here after a successful checkout."""
    session_id = request.GET.get('session_id')
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if session_id and settings.STRIPE_SECRET_KEY and not order.paid:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.get('payment_status') == 'paid':
                mark_order_paid_from_session(session)
                order.refresh_from_db()
        except stripe.error.StripeError:
            pass

    return render(request, 'store/order_success.html', {'order': order})


def payment_cancelled(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/payment_cancelled.html', {'order': order})


@csrf_exempt
def stripe_webhook(request):
    """Stripe calls this endpoint server-to-server to confirm payment events.
    Configure the endpoint URL + STRIPE_WEBHOOK_SECRET in the Stripe dashboard."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest('Invalid payload or signature')

    event_type = event.get('type') if isinstance(event, dict) else event['type']
    data_object = event['data']['object'] if isinstance(event, dict) else event.data.object

    if event_type == 'checkout.session.completed':
        mark_order_paid_from_session(data_object)

    return HttpResponse(status=200)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('store:home')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/order_history.html', {'orders': orders})


class StoreLoginView(LoginView):
    template_name = 'store/login.html'


class StoreLogoutView(LogoutView):
    next_page = 'store:home'
