from rest_framework import serializers

from .models import Review


class ReviewCreateSerializer(serializers.Serializer):
    product = serializers.CharField(help_text='Product Slug', read_only=True)
    user = serializers.CharField(read_only=True)
    rating = serializers.ChoiceField(choices=((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)))
    text = serializers.CharField(allow_blank=True)
