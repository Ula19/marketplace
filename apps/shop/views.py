from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response


from apps.shop.serializers import CategorySerializer, ProductSerializer
from apps.shop.models import Category, Product
from apps.sellers.models import Seller


tags = ["Shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary='Категории Получить',
        description="""
        Этот эндпоинт возвращает все категории.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary='Создание категории',
        description="""
        Этот эндпоинт создает категории.
        """,
        tags=tags,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(data=serializer.data, status=201)
        return Response(data=serializer.errors, status=400)


class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Категория Товары Получить",
        description="""
            Этот эндпоинт возвращает все продукты в определенной категории.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(data={"message": "Категория не существует!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="all_products",
        summary="Получение продукта",
        description="""
            Этот эндпоинт возвращает все продукты.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Продавец Товары Получить",
        description="""
            Этот эндпоинт возвращает все товары конкретного продавца.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(data={"message": "Продавец не существует!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Подробная информация о продукте",
        description="""
            Этот эндпоинт возвращает сведения о продукте через slug.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={"message": "Товар не существует!"}, status=404)
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)
