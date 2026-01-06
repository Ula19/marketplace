from django.contrib import admin

from .models import Seller



@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    pass
