"""
Thin wrapper around the Stripe SDK so views don't talk to Stripe directly.

Requires STRIPE_SECRET_KEY (and STRIPE_WEBHOOK_SECRET for webhook
verification) to be set as environment variables — see README.md.
"""

import stripe
from django.conf import settings
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeNotConfigured(Exception):
    """Raised when a card payment is attempted without API keys set."""
    pass


def create_checkout_session(request, order):
    """Create a Stripe Checkout Session for the given Order and return it."""
    if not settings.STRIPE_SECRET_KEY:
        raise StripeNotConfigured(
            'STRIPE_SECRET_KEY is not set. Add your Stripe test key as an '
            'environment variable to enable card payments.'
        )

    line_items = []
    for item in order.items.all():
        line_items.append({
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'unit_amount': int(item.price * 100),  # Stripe expects the smallest currency unit
                'product_data': {
                    'name': f'{item.product.name}' + (f' ({item.size})' if item.size else ''),
                },
            },
            'quantity': item.quantity,
        })

    success_url = request.build_absolute_uri(
        reverse('store:payment_success')
    ) + '?session_id={CHECKOUT_SESSION_ID}&order_id=' + str(order.id)
    cancel_url = request.build_absolute_uri(
        reverse('store:payment_cancelled', args=[order.id])
    )

    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=order.email,
        metadata={'order_id': order.id},
    )

    order.stripe_checkout_id = session.id
    order.save(update_fields=['stripe_checkout_id'])
    return session


def mark_order_paid_from_session(session):
    """Given a completed Stripe Checkout Session, mark the matching Order as paid."""
    from .models import Order  # local import to avoid circular import at module load

    order_id = session.get('metadata', {}).get('order_id')
    if not order_id:
        return None

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None

    order.paid = True
    order.status = 'paid'
    order.stripe_payment_intent = session.get('payment_intent', '') or ''
    order.save(update_fields=['paid', 'status', 'stripe_payment_intent'])
    return order
