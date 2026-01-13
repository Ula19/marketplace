from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.paginations import CustomPagination
from apps.common.permissions import IsStaff, IsSeller, IsOwner
from apps.shop.serializers import (CategorySerializer, ProductSerializer, OrderItemSerializer, ToggleCartItemSerializer,
                                   CheckoutSerializer, OrderSerializer)
from apps.shop.models import Category, Product
from apps.sellers.models import Seller
from apps.profiles.models import OrderItem, ShippingAddress, Order
from apps.shop.filters import ProductFilter
from apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE

tags = ["Shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer
    permission_classes = [IsStaff]
    throttle_scope = 'user'

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
    paginator_class = CustomPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'my_scope'

    @extend_schema(
        operation_id="all_products",
        summary="Получение продукта",
        description="""
            Этот эндпоинт возвращает все продукты.
        """,
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        filterset = ProductFilter(request.query_params, queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs
            paginator = self.paginator_class()
            paginated_queryset = paginator.paginate_queryset(queryset=queryset, request=request)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)


# @extend_schema(tags=tags)
# class ProductsView(ListAPIView):
#     serializer_class = ProductSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ProductFilter
#     pagination_class = CustomPagination
#
#     def get_queryset(self):
#         products = Product.objects.select_related("category", "seller", "seller__user").all()
#         return products


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [IsSeller]

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
    permission_classes = [IsAuthenticated]

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        self.check_object_permissions(self.request, product)
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


class CartView(APIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        summary="Товары в корзине",
        description="""
            Этот эндпоинт возвращает все товары в корзине пользователя.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user")
        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Переключить товар в корзине",
        description="""
            Этот эндпоинт позволяет пользователю или гостю добавлять/обновлять/удалять товар в корзине.
            Если количество равно 0, товар удаляется из корзины.
        """,
        tags=tags,
        request=ToggleCartItemSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=data["slug"])
        if not product:
            return Response({"message": "Нет продукта с таким slug"}, status=404)
        orderitem, created = OrderItem.objects.update_or_create(
            user=user,
            order=None,
            product=product,
            defaults={"quantity": quantity},
        )
        resp_message_substring = "Updated In"
        status_code = 200
        if created:
            status_code = 201
            resp_message_substring = "Added To"
        if orderitem.quantity == 0:
            resp_message_substring = "Removed From"
            orderitem.delete()
            data = None
        if resp_message_substring != "Removed From":
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(data={"message": f"Item {resp_message_substring} Cart", "item": data}, status=status_code)


class CheckoutView(APIView):
    serializer_class = CheckoutSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        summary="Проверить",
        description="""
               Этот эндпоинт позволяет пользователю создать заказ, посредством которого затем можно произвести оплату.
               """,
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self, request, *args, **kwargs):
        # Перейти к оформлению заказа
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None)
        if not orderitems.exists():
            return Response({"message": "В корзине нет товаров"}, status=404)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_id = data.get("shipping_id")
        # Получаем информацию о доставке на основе идентификатора доставки, введенного пользователем.
        shipping = ShippingAddress.objects.get_or_none(id=shipping_id)
        if not shipping:
            return Response({"message": "Нет адреса доставки с этим идентификатором."}, status=404)

        fields_to_update = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        ]
        data = {}
        for field in fields_to_update:
            value = getattr(shipping, field)
            data[field] = value

        order = Order.objects.create(user=user, **data)
        orderitems.update(order=order)

        serializer = OrderSerializer(order)
        return Response(data={"message": "Checkout Successful", "item": serializer.data}, status=200)
