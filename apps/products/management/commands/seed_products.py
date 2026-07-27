from django.core.management.base import BaseCommand

from apps.products.models import Category, Product
from apps.products.services import CategoryTreeService


class Command(BaseCommand):
    help = "Seeds a sample category tree and products for local development/testing."

    def handle(self, *args, **options):
        electronics, _ = Category.objects.get_or_create(slug='electronics', defaults={'name': 'Electronics'})
        phones, _ = Category.objects.get_or_create(slug='phones', defaults={'name': 'Phones', 'parent': electronics})
        laptops, _ = Category.objects.get_or_create(slug='laptops', defaults={'name': 'Laptops', 'parent': electronics})

        fashion, _ = Category.objects.get_or_create(slug='fashion', defaults={'name': 'Fashion'})
        mens, _ = Category.objects.get_or_create(slug='mens-wear', defaults={'name': "Men's Wear", 'parent': fashion})
        womens, _ = Category.objects.get_or_create(slug='womens-wear', defaults={'name': "Women's Wear", 'parent': fashion})

        products = [
            {'category': phones, 'name': 'Galaxy Z Fold 6', 'sku': 'PHN-001', 'price': 149000, 'stock': 15},
            {'category': phones, 'name': 'iPhone 16 Pro', 'sku': 'PHN-002', 'price': 168500, 'stock': 10},
            {'category': laptops, 'name': 'MacBook Air M4', 'sku': 'LPT-001', 'price': 132000, 'stock': 8},
            {'category': laptops, 'name': 'Dell XPS 14', 'sku': 'LPT-002', 'price': 145000, 'stock': 5},
            {'category': mens, 'name': "Men's Cotton Panjabi", 'sku': 'MEN-001', 'price': 1800, 'stock': 50},
            {'category': womens, 'name': "Women's Silk Saree", 'sku': 'WMN-001', 'price': 3200, 'stock': 30},
        ]

        created_count = 0
        for data in products:
            _, created = Product.objects.get_or_create(
                sku=data['sku'],
                defaults={
                    'category': data['category'],
                    'name': data['name'],
                    'price': data['price'],
                    'stock': data['stock'],
                },
            )
            if created:
                created_count += 1

        CategoryTreeService.invalidate()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded categories and {created_count} new product(s) (existing ones skipped)."
        ))
