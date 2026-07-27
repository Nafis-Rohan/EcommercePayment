import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category, Product

from .services import InsufficientStockError, OrderService

User = get_user_model()


class OrderModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.product = Product.objects.create(
            category=self.category, name='Widget', sku='WID-1', price=Decimal('9.99'), stock=10,
        )

    def test_calculate_totals_sums_subtotals(self):
        items = [{'unit_price': Decimal('10.00'), 'quantity': 2}, {'unit_price': Decimal('5.50'), 'quantity': 1}]
        total = OrderService.calculate_totals(items)
        self.assertEqual(total, Decimal('25.50'))

    def test_create_order_raises_on_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            OrderService.create_order(self.user, [{'product_id': self.product.id, 'quantity': 999}])

    def test_reduce_stock_for_order_decrements_stock(self):
        order = OrderService.create_order(self.user, [{'product_id': self.product.id, 'quantity': 3}])
        OrderService.reduce_stock_for_order(order)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)


class OrderAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='pass12345')
        self.other_user = User.objects.create_user(username='other', email='other@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat2', slug='cat2')
        self.product = Product.objects.create(
            category=self.category, name='Widget2', sku='WID-2', price=Decimal('9.99'), stock=10,
        )

    def test_create_order_requires_authentication(self):
        response = self.client.post(
            reverse('order-list-create'),
            {'items': [{'product_id': str(self.product.id), 'quantity': 1}]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('order-list-create'),
            {'items': [{'product_id': str(self.product.id), 'quantity': 2}]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_amount'], '19.98')

    def test_list_orders_scoped_to_own_user(self):
        OrderService.create_order(self.user, [{'product_id': self.product.id, 'quantity': 1}])
        OrderService.create_order(self.other_user, [{'product_id': self.product.id, 'quantity': 1}])

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('order-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class StockConcurrencyTests(TransactionTestCase):

    def setUp(self):
        self.category = Category.objects.create(name='Cat3', slug='cat3')
        self.product = Product.objects.create(
            category=self.category, name='Limited', sku='LIM-1', price=Decimal('10.00'), stock=1,
        )
        self.user = User.objects.create_user(username='racer', email='racer@example.com', password='pass12345')
        self.order_a = OrderService.create_order(self.user, [{'product_id': self.product.id, 'quantity': 1}])
        self.order_b = OrderService.create_order(self.user, [{'product_id': self.product.id, 'quantity': 1}])

    def test_only_one_concurrent_reduction_succeeds(self):
        results = {}

        def worker(name, order):
            try:
                OrderService.reduce_stock_for_order(order)
                results[name] = 'success'
            except InsufficientStockError:
                results[name] = 'failed'
            finally:
                connection.close()

        t1 = threading.Thread(target=worker, args=('a', self.order_a))
        t2 = threading.Thread(target=worker, args=('b', self.order_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(sorted(results.values()), ['failed', 'success'])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
