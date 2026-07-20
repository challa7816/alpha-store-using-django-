from .cart import Cart
from .models import Category


def cart(request):
    return {'cart': Cart(request)}


def categories(request):
    return {'categories_nav': Category.objects.all()}
