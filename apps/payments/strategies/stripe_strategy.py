import stripe
from django.conf import settings

from .base import PaymentStrategy

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeStrategy(PaymentStrategy):
    def initiate(self, **kwargs):
        order = self.payment.order
        intent = stripe.PaymentIntent.create(
            amount=int(order.total_amount * 100),  # Stripe wants the amount in cents
            currency='usd',
            payment_method_types=['card'],
            metadata={'order_id': str(order.id), 'payment_id': str(self.payment.id)},
        )


        self.payment.transaction_id = intent.id
        self.payment.raw_response = intent
        self.payment.save(update_fields=['transaction_id', 'raw_response'])

        return {'client_secret': intent.client_secret}

    def confirm(self, **kwargs):
        intent = stripe.PaymentIntent.retrieve(self.payment.transaction_id)
        self.payment.raw_response = intent
        self.payment.save(update_fields=['raw_response'])
        return intent

    def verify(self, payload, sig_header):
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        intent = event['data']['object']

        self.payment.raw_response = intent
        self.payment.save(update_fields=['raw_response'])

        return intent['status'] == 'succeeded'
