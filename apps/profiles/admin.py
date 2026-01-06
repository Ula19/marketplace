from django.contrib import admin

from .models import ShippingAddress, Order, OrderItem


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass



@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass
