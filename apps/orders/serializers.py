from rest_framework import serializers

from apps.products.models import Product

from .models import Order, OrderItem
from .services import InsufficientStockError, OrderService


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_amount', 'items', 'created_at', 'updated_at']
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            order = OrderService.create_order(
                user=user,
                items=[
                    {'product_id': item['product_id'].id, 'quantity': item['quantity']}
                    for item in validated_data['items']
                ],
            )
        except InsufficientStockError as exc:
            raise serializers.ValidationError(str(exc))
        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data
