from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel
from apps.common.utils import generate_unique_code
from apps.shop.models import Product


class ShippingAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=12)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=6)

    def __str__(self):
        return f"{self.full_name}'s shipping details"


DELIVERY_STATUS_CHOICES = (
    ("PENDING", "В ОЖИДАНИИ"),
    ("PACKING", "УПАКОВКА"),
    ("SHIPPING", "ПЕРЕВОЗКA"),
    ("ARRIVING", "ПРИБЫТИЕ"),
    ("SUCCESS", "УСПЕХ"),
)

PAYMENT_STATUS_CHOICES = (
    ("PENDING", "В ОЖИДАНИИ"),
    ("PROCESSING", "ОБРАБОТКА"),
    ("SUCCESSFUL", "УСПЕШНЫЙ"),
    ("CANCELLED", "ОТМЕНЕНО"),
    ("FAILED", "НЕУСПЕШНЫЙ"),
)


class Order(BaseModel):
    """
    Represents a customer's order.

    Attributes:
        user (ForeignKey): The user who placed the order.
        tx_ref (str): The unique transaction reference.
        delivery_status (str): The delivery status of the order.
        payment_status (str): The payment status of the order.

    Methods:
        __str__():
            Returns a string representation of the transaction reference.
        save(*args, **kwargs):
            Overrides the save method to generate a unique transaction reference when a new order is created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    tx_ref = models.CharField(max_length=100, blank=True, unique=True)
    delivery_status = models.CharField(max_length=20, default='PENDING', choices=DELIVERY_STATUS_CHOICES)
    payment_status = models.CharField(max_length=20, default='PENDING', choices=PAYMENT_STATUS_CHOICES)
    date_delivered = models.DateTimeField(null=True, blank=True)

    # Shipping address details
    full_name = models.CharField(max_length=1000, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(null=True, max_length=20)
    address = models.CharField(null=True, max_length=1000)
    city = models.CharField(null=True, max_length=200)
    country = models.CharField(null=True, max_length=100)
    zipcode = models.CharField(null=True, max_length=6)


    def __str__(self):
        return f'{self.user.full_name}\'s order'

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.tx_ref = generate_unique_code(Order, 'tx_ref')
        super().save(*args, **kwargs)

    @property
    def get_cart_subtotal(self):
        orderitems = self.orderitems.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_total(self):
        total = self.get_cart_subtotal
        return total


class OrderItem(BaseModel):
    """
    Represents an item within an order.

    Attributes:
        order (ForeignKey): The order to which this item belongs.
        product (ForeignKey): The product associated with this order item.
        quantity (int): The quantity of the product ordered.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitems', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-created_at']

    @property
    def get_total(self):
        return self.product.price_current * self.quantity

    def __str__(self):
        return self.product.name
