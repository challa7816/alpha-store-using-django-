from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('products/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    path('checkout/', views.order_create, name='order_create'),
    path('orders/', views.order_history, name='order_history'),

    path('payment/<int:order_id>/checkout/', views.payment_checkout, name='payment_checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/<int:order_id>/cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('payment/webhook/', views.stripe_webhook, name='stripe_webhook'),

    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.StoreLoginView.as_view(), name='login'),
    path('accounts/logout/', views.StoreLogoutView.as_view(), name='logout'),
]
