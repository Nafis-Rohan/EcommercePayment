import logging
from decimal import Decimal

from django.db import transaction

from apps.orders.models import Order, OrderItem
from apps.products.models import Product

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    pass


class OrderService:
    @staticmethod
    def calculate_totals(items_data):
        total = Decimal('0')
        for item in items_data:
            item['subtotal'] = item['unit_price'] * item['quantity']
            total += item['subtotal']
        return total

    @classmethod
    @transaction.atomic
    def create_order(cls, user, items):
        ordered_items = sorted(items, key=lambda i: str(i['product_id']))

        items_data = []
        for item in ordered_items:
            product = Product.objects.select_for_update().get(id=item['product_id'])
            quantity = item['quantity']

            if product.stock < quantity:
                raise InsufficientStockError(f"Insufficient stock for '{product.name}'")

            items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': product.price,
            })

        total = cls.calculate_totals(items_data)

        order = Order.objects.create(user=user, total_amount=total)
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=data['product'],
                quantity=data['quantity'],
                unit_price=data['unit_price'],
                subtotal=data['subtotal'],
            )
            for data in items_data
        ])

        logger.info("Order %s created for user %s (total=%s)", order.id, user.id, total)
        return order

    @classmethod
    @transaction.atomic
    def reduce_stock_for_order(cls, order):
        items = list(order.items.all())
        product_ids = sorted({item.product_id for item in items}, key=str)
        products = {
            p.id: p
            for p in Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
        }

        for item in items:
            product = products[item.product_id]
            if product.stock < item.quantity:
                logger.error(
                    "Insufficient stock reducing order %s: product %s has %s, needs %s",
                    order.id, product.id, product.stock, item.quantity,
                )
                raise InsufficientStockError(f"Insufficient stock for '{product.name}'")

        for item in items:
            product = products[item.product_id]
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        logger.info("Stock reduced for order %s after successful payment", order.id)
