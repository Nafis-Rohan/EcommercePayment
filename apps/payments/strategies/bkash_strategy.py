import requests
from django.conf import settings
from django.core.cache import cache

from .base import PaymentStrategy

BKASH_TOKEN_CACHE_KEY = 'bkash_id_token'


class BkashStrategy(PaymentStrategy):
    def _headers(self, token):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
            'X-APP-Key': settings.BKASH_APP_KEY,
        }

    def _grant_token(self):
        token = cache.get(BKASH_TOKEN_CACHE_KEY)
        if token:
            return token

        response = requests.post(
            f"{settings.BKASH_BASE_URL}/tokenized/checkout/token/grant",
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'username': settings.BKASH_USERNAME,
                'password': settings.BKASH_PASSWORD,
            },
            json={
                'app_key': settings.BKASH_APP_KEY,
                'app_secret': settings.BKASH_APP_SECRET,
            },
        )
        response.raise_for_status()
        data = response.json()

        token = data['id_token']
        cache.set(BKASH_TOKEN_CACHE_KEY, token, timeout=data.get('expires_in', 3600) - 60)
        return token

    def initiate(self, callback_url, **kwargs):
        order = self.payment.order
        token = self._grant_token()

        response = requests.post(
            f"{settings.BKASH_BASE_URL}/tokenized/checkout/create",
            headers=self._headers(token),
            json={
                'mode': '0011',
                'payerReference': str(order.user_id),
                'callbackURL': callback_url,
                'amount': str(order.total_amount),
                'currency': 'BDT',
                'intent': 'sale',
                'merchantInvoiceNumber': str(order.id),
            },
        )
        response.raise_for_status()
        data = response.json()

        self.payment.transaction_id = data.get('paymentID')
        self.payment.raw_response = data
        self.payment.save(update_fields=['transaction_id', 'raw_response'])

        return {'bkash_url': data.get('bkashURL')}

    def confirm(self, **kwargs):
        token = self._grant_token()
        response = requests.post(
            f"{settings.BKASH_BASE_URL}/tokenized/checkout/execute/{self.payment.transaction_id}",
            headers=self._headers(token),
        )
        response.raise_for_status()
        data = response.json()

        self.payment.raw_response = data
        self.payment.save(update_fields=['raw_response'])

        return data.get('transactionStatus') == 'Completed'

    def verify(self, **kwargs):
        token = self._grant_token()
        response = requests.post(
            f"{settings.BKASH_BASE_URL}/tokenized/checkout/payment/status/{self.payment.transaction_id}",
            headers=self._headers(token),
        )
        response.raise_for_status()
        data = response.json()

        self.payment.raw_response = data
        self.payment.save(update_fields=['raw_response'])

        return data.get('transactionStatus') == 'Completed'
