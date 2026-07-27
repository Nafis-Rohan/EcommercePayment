from rest_framework import generics, permissions

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.all().order_by('-created_at')
        if user.is_staff:
            return qs
        return qs.filter(user=user)
