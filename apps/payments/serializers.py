from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'provider', 'transaction_id', 'status', 'raw_response', 'created_at', 'updated_at']
        read_only_fields = fields
