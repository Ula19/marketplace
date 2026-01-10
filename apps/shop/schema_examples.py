from drf_spectacular.utils import OpenApiParameter, OpenApiTypes



PRODUCT_PARAM_EXAMPLE = [
    OpenApiParameter(
        name="max_price",
        description="Фильтровать товары по MAX текущей цене",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="min_price",
        description="Фильтровать товары по минимальной текущей цене",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="in_stock",
        description="Фильтровать товары по ассортименту",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="name",
        description="Фильтровать товары по названию",
        required=False,
        type=OpenApiTypes.STR,
    ),
]
