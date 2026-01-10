import django_filters
from django.contrib.postgres.search import TrigramSimilarity

from .models import Product



class ProductFilter(django_filters.FilterSet):
    max_price = django_filters.NumberFilter(field_name='price_current', lookup_expr='lte')
    min_price = django_filters.NumberFilter(field_name='price_current', lookup_expr='gte')
    in_stock = django_filters.NumberFilter(lookup_expr='gte')
    name = django_filters.CharFilter(field_name='name', method='filter_name_trigram')
    # created_at = django_filters.DateTimeFilter(lookup_expr='gte')

    class Meta:
        model = Product
        fields = ['max_price', 'min_price', 'in_stock', 'name',]

    def filter_name_trigram(self, queryset, name, value):
        if value:
            return queryset.annotate(
                similarity=TrigramSimilarity('name', value)
            ).filter(similarity__gt=0.1).order_by('-similarity')
        return queryset
