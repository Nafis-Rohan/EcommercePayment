from django.db import models

from apps.common.models import BaseModel
from apps.orders.models import Order


class Payment(BaseModel):
    PROVIDER_STRIPE = 'stripe'
    PROVIDER_BKASH = 'bkash'
    PROVIDER_CHOICES = [
        (PROVIDER_STRIPE, 'Stripe'),
        (PROVIDER_BKASH, 'bKash'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.provider} payment for order {self.order_id}"
