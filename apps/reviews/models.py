from django.db import models

from apps.common.models import IsDeletedModel
from apps.accounts.models import User
from apps.shop.models import Product


class Review(IsDeletedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)))
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f'{self.user.full_name}--{self.product.name}'
