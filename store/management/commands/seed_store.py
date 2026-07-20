from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product, Review

CATEGORIES = ['Men', 'Women', 'Kids', 'Accessories']

PRODUCTS = [
    ('Men', 'Classic Oxford Shirt', 1499.00, None, 'White', 'S,M,L,XL', 40,
     'A crisp cotton oxford shirt cut for everyday wear.'),
    ('Men', 'Slim Fit Chinos', 1899.00, 1599.00, 'Khaki', 'S,M,L,XL,XXL', 25,
     'Tapered chinos in a durable cotton-stretch blend.'),
    ('Men', 'Merino Crew Sweater', 2999.00, None, 'Charcoal', 'M,L,XL', 15,
     'Lightweight merino wool sweater for cool days.'),
    ('Women', 'Linen Wrap Dress', 2499.00, None, 'Terracotta', 'XS,S,M,L', 20,
     'Breathable linen dress with an adjustable wrap tie.'),
    ('Women', 'High-Rise Straight Jeans', 2199.00, 1799.00, 'Indigo', 'S,M,L,XL', 30,
     'Rigid denim with a clean, high-rise silhouette.'),
    ('Women', 'Silk Blend Blouse', 1999.00, None, 'Ivory', 'XS,S,M,L', 18,
     'A soft silk-blend blouse for work or evening.'),
    ('Kids', 'Graphic Tee Set (2-pack)', 899.00, None, 'Multicolor', 'S,M,L', 50,
     'Two soft cotton tees with playful prints.'),
    ('Kids', 'Fleece Zip Hoodie', 1299.00, None, 'Navy', 'S,M,L', 22,
     'Warm fleece hoodie built for the playground.'),
    ('Accessories', 'Leather Belt', 999.00, None, 'Brown', '', 60,
     'Full-grain leather belt with a brushed buckle.'),
    ('Accessories', 'Wool Beanie', 599.00, None, 'Grey', '', 45,
     'A ribbed wool beanie for cold mornings.'),
    ('Men', 'Denim Trucker Jacket', 2799.00, 2299.00, 'Mid Blue', 'S,M,L,XL', 18,
     'A classic denim jacket with a broken-in wash and sturdy stitching.'),
    ('Women', 'Cropped Knit Cardigan', 1699.00, None, 'Cream', 'XS,S,M,L', 24,
     'A soft cropped cardigan that layers easily over any outfit.'),
    ('Kids', 'Printed Rain Jacket', 1099.00, None, 'Yellow', 'S,M,L', 30,
     'A lightweight, water-resistant jacket with a playful print.'),
]

DEMO_REVIEWERS = [
    ('priya_k', 'priya_k@example.com'),
    ('rahul_m', 'rahul_m@example.com'),
    ('ananya_s', 'ananya_s@example.com'),
]

SAMPLE_COMMENTS = [
    (5, 'Fit was perfect and the fabric feels premium. Would buy again.'),
    (4, 'Good quality overall, sizing runs slightly large.'),
    (5, 'Exactly as pictured, fast delivery too.'),
]


class Command(BaseCommand):
    help = 'Seeds the database with sample categories, products, and reviews for the ALPHA STORE clothing store.'

    def handle(self, *args, **options):
        category_map = {}
        for name in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name, defaults={'slug': slugify(name)}
            )
            category_map[name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))

        created_products = []
        for cat_name, name, price, discount, color, sizes, stock, desc in PRODUCTS:
            slug = slugify(name)
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'category': category_map[cat_name],
                    'name': name,
                    'description': desc,
                    'price': price,
                    'discount_price': discount,
                    'color': color,
                    'available_sizes': sizes,
                    'stock': stock,
                    'available': True,
                }
            )
            created_products.append(product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {name}'))

        # Create a few demo reviewer accounts (password: alphastore123)
        reviewers = []
        for username, email in DEMO_REVIEWERS:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            if created:
                user.set_password('alphastore123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created demo reviewer: {username}'))
            reviewers.append(user)

        # Sprinkle a couple of sample reviews across the first few products
        for i, product in enumerate(created_products[:6]):
            reviewer = reviewers[i % len(reviewers)]
            rating, comment = SAMPLE_COMMENTS[i % len(SAMPLE_COMMENTS)]
            _, created = Review.objects.get_or_create(
                product=product, user=reviewer,
                defaults={'rating': rating, 'comment': comment}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added review for: {product.name}'))

        self.stdout.write(self.style.SUCCESS('Store seeded successfully.'))
