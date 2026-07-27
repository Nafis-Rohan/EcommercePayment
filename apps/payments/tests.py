import json
from decimal import Decimal
from unittest.mock import patch

import stripe
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.products.models import Category, Product

from .models import Payment

User = get_user_model()


class FakeStripeObject(dict):
    """Mimics stripe's StripeObject enough for our code: dict + attribute access, JSON-serializable."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def _make_order(user, product, quantity=1):
    return OrderService.create_order(user, [{'product_id': product.id, 'quantity': quantity}])


class PaymentModelTests(TestCase):
    """Unit test for the Payment model."""

    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.product = Product.objects.create(
            category=self.category, name='Widget', sku='WID-1', price=Decimal('9.99'), stock=10,
        )
        self.order = _make_order(self.user, self.product)

    def test_transaction_id_must_be_unique(self):
        Payment.objects.create(order=self.order, provider=Payment.PROVIDER_STRIPE, transaction_id='dup-id')
        with self.assertRaises(IntegrityError):
            Payment.objects.create(order=self.order, provider=Payment.PROVIDER_STRIPE, transaction_id='dup-id')


class PaymentAPITests(APITestCase):
    """API tests for payments (checkout + viewing own payments)."""

    def setUp(self):
        self.user = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='pass12345')
        self.other_user = User.objects.create_user(username='other2', email='other2@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat2', slug='cat2')
        self.product = Product.objects.create(
            category=self.category, name='Widget2', sku='WID-2', price=Decimal('20.00'), stock=5,
        )
        self.order = _make_order(self.user, self.product)
        self.other_order = _make_order(self.other_user, self.product)

    def test_checkout_requires_authentication(self):
        response = self.client.post(
            reverse('payment-checkout'), {'order_id': str(self.order.id), 'provider': 'stripe'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.payments.strategies.stripe_strategy.stripe.PaymentIntent.create')
    def test_checkout_stripe_creates_payment(self, mock_create):
        mock_create.return_value = FakeStripeObject({
            'id': 'pi_123', 'client_secret': 'secret_123', 'status': 'requires_payment_method',
        })
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('payment-checkout'), {'order_id': str(self.order.id), 'provider': 'stripe'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.get(id=response.data['payment_id'])
        self.assertEqual(payment.transaction_id, 'pi_123')

    def test_list_payments_scoped_to_own_user(self):
        Payment.objects.create(order=self.order, provider=Payment.PROVIDER_STRIPE)
        Payment.objects.create(order=self.other_order, provider=Payment.PROVIDER_STRIPE)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('payment-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class StripeWebhookTests(APITestCase):
    """Webhook test cases — Stripe."""

    def setUp(self):
        self.user = User.objects.create_user(username='buyer3', email='buyer3@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat3', slug='cat3')
        self.product = Product.objects.create(
            category=self.category, name='Widget3', sku='WID-3', price=Decimal('15.00'), stock=3,
        )
        self.order = _make_order(self.user, self.product, quantity=2)
        self.payment = Payment.objects.create(
            order=self.order, provider=Payment.PROVIDER_STRIPE, transaction_id='pi_webhook_1'
        )

    @patch('apps.payments.strategies.stripe_strategy.stripe.Webhook.construct_event')
    def test_webhook_success_marks_paid_and_reduces_stock(self, mock_construct_event):
        mock_construct_event.return_value = {
            'data': {'object': {'id': self.payment.transaction_id, 'status': 'succeeded'}}
        }
        payload = json.dumps({'data': {'object': {'id': self.payment.transaction_id}}}).encode()

        response = self.client.post(
            reverse('stripe-webhook'), data=payload, content_type='application/json',
            HTTP_STRIPE_SIGNATURE='fake-sig',
        )
        self.assertEqual(response.status_code, 200)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.product.stock, 1)  # 3 - 2

    @patch('apps.payments.strategies.stripe_strategy.stripe.Webhook.construct_event')
    def test_webhook_bad_signature_returns_400(self, mock_construct_event):
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError('bad sig', 'sig_header')
        payload = json.dumps({'data': {'object': {'id': self.payment.transaction_id}}}).encode()

        response = self.client.post(
            reverse('stripe-webhook'), data=payload, content_type='application/json',
            HTTP_STRIPE_SIGNATURE='fake-sig',
        )
        self.assertEqual(response.status_code, 400)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)


class BkashCallbackTests(APITestCase):
    """Webhook/callback test case — bKash."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='buyer4', email='buyer4@example.com', password='pass12345')
        self.category = Category.objects.create(name='Cat4', slug='cat4')
        self.product = Product.objects.create(
            category=self.category, name='Widget4', sku='WID-4', price=Decimal('12.00'), stock=4,
        )
        self.order = _make_order(self.user, self.product, quantity=1)
        self.payment = Payment.objects.create(
            order=self.order, provider=Payment.PROVIDER_BKASH, transaction_id='bkash_txn_1'
        )

    @patch('apps.payments.strategies.bkash_strategy.requests.post')
    def test_callback_success_marks_paid_and_reduces_stock(self, mock_post):
        def fake_post(url, headers=None, json=None, **kwargs):
            if url.endswith('/tokenized/checkout/token/grant'):
                return FakeResponse({'id_token': 'tok123', 'expires_in': 3600})
            if '/tokenized/checkout/execute/' in url:
                return FakeResponse({'transactionStatus': 'Completed'})
            raise AssertionError(f'Unexpected bKash URL: {url}')

        mock_post.side_effect = fake_post

        url = reverse('bkash-callback') + f'?paymentID={self.payment.transaction_id}&status=success'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.product.stock, 3)  # 4 - 1
