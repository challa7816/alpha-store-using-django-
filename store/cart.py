from decimal import Decimal

from django.conf import settings

from .models import Product


class Cart:
    """A session-based shopping cart for the clothing store."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def _key(self, product_id, size):
        return f'{product_id}_{size or "onesize"}'

    def add(self, product, quantity=1, size='', update_quantity=False):
        key = self._key(product.id, size)
        if key not in self.cart:
            self.cart[key] = {
                'product_id': product.id,
                'quantity': 0,
                'price': str(product.current_price),
                'size': size,
            }
        if update_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product, size=''):
        key = self._key(product.id, size)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)
        products_map = {p.id: p for p in products}

        cart = self.cart.copy()
        for item in cart.values():
            item = item.copy()
            item['product'] = products_map[item['product_id']]
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity'] for item in self.cart.values()
        )

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
