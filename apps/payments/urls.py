from django.urls import path

from .views import (
    BkashCallbackView,
    BkashPaymentStatusView,
    CheckoutView,
    PaymentDetailView,
    PaymentListView,
    StripeWebhookView,
)

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('checkout/', CheckoutView.as_view(), name='payment-checkout'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('bkash/callback/', BkashCallbackView.as_view(), name='bkash-callback'),
    path('<uuid:pk>/bkash/status/', BkashPaymentStatusView.as_view(), name='bkash-payment-status'),
    path('<uuid:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
]
