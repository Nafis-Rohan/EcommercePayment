import json
import logging

import requests
import stripe
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.services import InsufficientStockError, OrderService

from .models import Payment
from .serializers import PaymentSerializer
from .services import PaymentService, UnsupportedProviderError

logger = logging.getLogger(__name__)


def _mark_failed(payment):
    payment.status = Payment.STATUS_FAILED
    payment.save(update_fields=['status'])
    order = payment.order
    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=['status'])


def _mark_paid(payment):
    order = payment.order

    try:
        OrderService.reduce_stock_for_order(order)
    except InsufficientStockError:
        logger.error("Payment %s succeeded but stock is unavailable for order %s", payment.id, order.id)
        _mark_failed(payment)
        return False

    payment.status = Payment.STATUS_SUCCESS
    payment.save(update_fields=['status'])
    order.status = Order.STATUS_PAID
    order.save(update_fields=['status'])
    return True


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related('order').order_by('-created_at')
        if user.is_staff:
            return qs
        return qs.filter(order__user=user)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related('order')
        if user.is_staff:
            return qs
        return qs.filter(order__user=user)


class BkashPaymentStatusView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        qs = Payment.objects.select_related('order')
        if not request.user.is_staff:
            qs = qs.filter(order__user=request.user)
        payment = get_object_or_404(qs, pk=pk, provider=Payment.PROVIDER_BKASH)

        try:
            succeeded = PaymentService.verify_payment(payment)
        except requests.RequestException as exc:
            logger.error("bKash status query failed for payment %s: %s", payment.id, exc)
            return Response({'detail': 'Could not query payment status.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'payment_id': payment.id,
            'transaction_id': payment.transaction_id,
            'bkash_transaction_status': payment.raw_response.get('transactionStatus'),
            'succeeded': succeeded,
        })


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order = get_object_or_404(Order, id=request.data.get('order_id'), user=request.user)
        provider = request.data.get('provider')

        kwargs = {}
        if provider == Payment.PROVIDER_BKASH:
            kwargs['callback_url'] = request.build_absolute_uri(reverse('bkash-callback'))

        try:
            payment, result = PaymentService.initiate_payment(order, provider, **kwargs)
        except UnsupportedProviderError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (requests.RequestException, stripe.error.StripeError) as exc:
            logger.error("Payment initiation failed for order %s (%s): %s", order.id, provider, exc)
            return Response(
                {'detail': 'Payment provider error. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'payment_id': payment.id, **result},
            status=status.HTTP_201_CREATED,
        )


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            intent_id = json.loads(payload)['data']['object']['id']
        except (ValueError, KeyError):
            return HttpResponse(status=400)

        payment = Payment.objects.filter(transaction_id=intent_id).first()
        if payment is None:
            return HttpResponse(status=404)

        try:
            succeeded = PaymentService.verify_payment(payment, payload=payload, sig_header=sig_header)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if succeeded:
            if not _mark_paid(payment):
                logger.warning("Stripe payment %s succeeded but order could not be fulfilled (stock).", payment.id)
        else:
            logger.info("Stripe payment %s failed; cancelling order %s.", payment.id, payment.order_id)
            _mark_failed(payment)

        return HttpResponse(status=200)


class BkashCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        payment = get_object_or_404(Payment, transaction_id=request.query_params.get('paymentID'))

        if request.query_params.get('status') != 'success':
            _mark_failed(payment)
            return Response({'detail': 'Payment not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            succeeded = PaymentService.confirm_payment(payment)
        except requests.RequestException as exc:
            logger.error("bKash execute call failed for payment %s: %s", payment.id, exc)
            _mark_failed(payment)
            return Response({'detail': 'Payment execution failed.'}, status=status.HTTP_400_BAD_REQUEST)

        if succeeded:
            if _mark_paid(payment):
                return Response({'detail': 'Payment successful.', 'order_id': payment.order_id})
            return Response(
                {'detail': 'Payment succeeded but stock is unavailable; contact support.'},
                status=status.HTTP_409_CONFLICT,
            )

        _mark_failed(payment)
        return Response({'detail': 'Payment execution failed.'}, status=status.HTTP_400_BAD_REQUEST)
