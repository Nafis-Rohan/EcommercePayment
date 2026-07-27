import requests
import stripe

from apps.orders.models import Order

from .models import Payment
from .strategies.bkash_strategy import BkashStrategy
from .strategies.stripe_strategy import StripeStrategy


class UnsupportedProviderError(Exception):
    pass


class PaymentService:
    STRATEGIES = {
        Payment.PROVIDER_STRIPE: StripeStrategy,
        Payment.PROVIDER_BKASH: BkashStrategy,
    }

    @classmethod
    def get_strategy(cls, payment):
        strategy_class = cls.STRATEGIES.get(payment.provider)
        if strategy_class is None:
            raise UnsupportedProviderError(f"No strategy registered for provider '{payment.provider}'")
        return strategy_class(payment)

    @classmethod
    def initiate_payment(cls, order: Order, provider: str, **kwargs):
        payment = Payment.objects.create(order=order, provider=provider)
        strategy = cls.get_strategy(payment)
        try:
            result = strategy.initiate(**kwargs)
        except (requests.RequestException, stripe.error.StripeError):
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=['status'])
            raise
        return payment, result

    @classmethod
    def confirm_payment(cls, payment: Payment, **kwargs):
        strategy = cls.get_strategy(payment)
        return strategy.confirm(**kwargs)

    @classmethod
    def verify_payment(cls, payment: Payment, **kwargs):
        strategy = cls.get_strategy(payment)
        return strategy.verify(**kwargs)
