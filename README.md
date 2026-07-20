# ALPHA STORE — Django Clothing E-Commerce Platform

A full-stack e-commerce web application for an online clothing store, built with
**Python**, **Django**, **SQL (SQLite via Django ORM)**, **HTML**, and **CSS**.

## Features

- Product catalog with categories, sizes, colors, stock, and sale pricing
- Product search and filter by category
- **Product detail pages with "You might also like" recommendations**
- **Cross-sell recommendations on the cart page**
- **Star-rated customer reviews** (one review per customer per product, editable)
- Session-based shopping cart (add, update quantity, remove)
- Full checkout flow that creates an Order + OrderItems in the database
- **Payment integration**: Cash on Delivery, and real Card payments via **Stripe Checkout**
  (with a Stripe webhook for reliable payment confirmation)
- User registration, login, logout (Django auth)
- Order history for logged-in customers, including payment status
- Django admin panel for managing categories, products, orders, and reviews
- Responsive, custom-designed UI (no external CSS frameworks)

## Tech stack

| Layer      | Technology            |
|------------|------------------------|
| Backend    | Python 3 + Django 4.2  |
| Database   | SQLite (Django ORM / SQL) |
| Payments   | Stripe Checkout + Webhooks |
| Frontend   | HTML5 + CSS3 (Django templates) |
| Auth       | Django's built-in authentication |

## Project structure

```
alpha_django/
├── manage.py
├── requirements.txt
├── ecommerce/                # Project settings, root URLs
│   ├── settings.py           # includes Stripe config
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── store/                    # Main e-commerce app
    ├── models.py              # Category, Product, Order, OrderItem, Review
    ├── views.py                # Pages, cart, checkout, payments, reviews
    ├── payments.py              # Stripe Checkout Session helpers
    ├── urls.py
    ├── forms.py
    ├── cart.py                  # Session cart class
    ├── admin.py
    ├── management/commands/seed_store.py   # sample products + demo reviews
    ├── templates/store/         # HTML templates
    └── static/store/css/style.css          # Stylesheet
```

## Setup instructions

1. **Unzip the project** and move into the folder:
   ```bash
   cd alpha_django
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations** (creates the SQLite tables):
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create an admin (superuser) account:**
   ```bash
   python manage.py createsuperuser
   ```

6. **(Optional) Load sample products, categories, and demo reviews:**
   ```bash
   python manage.py seed_store
   ```
   This also creates three demo reviewer accounts (`priya_k`, `rahul_m`,
   `ananya_s` — password `alphastore123`) already carrying reviews on a few
   products, so ratings show up immediately.

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

8. Visit the app:
   - Storefront: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Setting up card payments (Stripe)

Card payments work out of the box once you provide Stripe test API keys as
environment variables. **Cash on Delivery works immediately with no setup.**

1. Create a free Stripe account and grab your **test mode** keys from
   https://dashboard.stripe.com/test/apikeys
2. Export them before running the server:
   ```bash
   export STRIPE_PUBLISHABLE_KEY="pk_test_..."
   export STRIPE_SECRET_KEY="sk_test_..."
   ```
3. To have orders automatically marked "paid" (recommended), set up a webhook:
   - In the Stripe dashboard: Developers → Webhooks → Add endpoint
   - Endpoint URL: `https://<your-domain>/payment/webhook/`
   - Event to send: `checkout.session.completed`
   - Copy the generated signing secret and export it too:
     ```bash
     export STRIPE_WEBHOOK_SECRET="whsec_..."
     ```
   - For local testing, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):
     ```bash
     stripe listen --forward-to localhost:8000/payment/webhook/
     ```
4. Use Stripe's test card `4242 4242 4242 4242`, any future expiry date, and
   any CVC to simulate a successful payment.

If `STRIPE_SECRET_KEY` isn't set, choosing "Pay by Card" at checkout will show
a friendly message instead of crashing, explaining that keys need to be
configured — Cash on Delivery continues to work regardless.

## How the payment flow works

1. Shopper checks out and picks **Cash on Delivery** or **Pay by Card**.
2. An `Order` + `OrderItem` rows are always created immediately in the database.
3. For COD, the order is confirmed right away (`paid=False`, awaiting delivery).
4. For Card, the shopper is redirected to a Stripe-hosted Checkout page built
   from the order's line items.
5. On success, Stripe redirects back to `/payment/success/`, and (more
   reliably) sends a `checkout.session.completed` event to the webhook —
   either path flips the order to `paid=True`.
6. On cancellation, the shopper lands on a "Payment cancelled" page with a
   **Retry payment** button — the order isn't lost.

## Reviews

- Any logged-in user can leave **one rating (1–5 stars) + optional comment**
  per product; resubmitting updates their existing review instead of
  duplicating it.
- Average rating and review count are shown on product cards and the product
  detail page.
- All reviews are moderated from the Django admin (`Reviews` section).

## Recommendations

- Product detail pages show a **"You might also like"** row of related items
  from the same category (falling back to other available products if a
  category is small).
- The cart page shows a **"Complete the look"** row of items related to what's
  already in the cart, excluding items already added.

## Adding your own images (hero banner + category tiles)

The homepage now shows real images instead of placeholder boxes:

- **Hero banner** ("ALPHA STORE SS26 COLLECTION" box): this is a plain static
  file, so there's no admin step needed — just replace this file with your
  own picture (keep the same filename, ideally a portrait image around
  900×1125px or similar 4:5 ratio):
  ```
  store/static/store/img/hero.jpg
  ```

- **Category tiles** (Accessories, Kids, Men, Women): also plain static
  files — replace these four files with your own pictures (same 4:5 portrait
  ratio works best):
  ```
  store/static/store/img/category-accessories.jpg
  store/static/store/img/category-kids.jpg
  store/static/store/img/category-men.jpg
  store/static/store/img/category-women.jpg
  ```
  Placeholder images are included so nothing looks broken until you swap them in.

  If you'd rather manage category images from the Django admin instead of
  static files, each `Category` now also has an optional `image` field —
  upload one there and it will automatically be used instead of the static
  file. To enable this, run migrations again after unzipping:
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- **Product photos** (featured pieces, product pages): these already come
  from the `image` field on each `Product`, uploaded via `/admin/`. Three new
  sample products (Denim Trucker Jacket, Cropped Knit Cardigan, Printed Rain
  Jacket) were added to `seed_store.py` — run `python manage.py seed_store`
  again to load them, then open `/admin/` → **Products** to upload a photo
  for each one (and any others still missing a picture). The homepage now
  shows up to 11 featured pieces instead of 8.

## Adding products

Log into `/admin/` with your superuser account, then add **Categories** first,
followed by **Products**. Each product can have a size list (comma separated,
e.g. `S,M,L,XL`), a color, stock count, and an optional sale (`discount_price`).

## Notes

- The cart is stored in the user's session, so it works for both guests and
  logged-in users.
- `DEBUG = True` and `SECRET_KEY` in `ecommerce/settings.py` are set for local
  development only — change both, disable `DEBUG`, and set real environment
  variables before deploying to production.
