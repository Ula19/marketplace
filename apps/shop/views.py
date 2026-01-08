from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsStaff, IsSeller, IsOwner
from apps.shop.serializers import (CategorySerializer, ProductSerializer, OrderItemSerializer, ToggleCartItemSerializer,
                                   CheckoutSerializer, OrderSerializer)
from apps.shop.models import Category, Product
from apps.sellers.models import Seller
from apps.profiles.models import OrderItem, ShippingAddress, Order


tags = ["Shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer
    permission_classes = [IsStaff]

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

    @extend_schema(
        operation_id="all_products",
        summary="Получение продукта",
        description="""
            Этот эндпоинт возвращает все продукты.
        """,
        tags=tags,
        parameters=[
            OpenApiParameter(
                name='max_price',
                description='Фильтровать товары по MAX текущей цене',
                required=False,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="min_price",
                description="Фильтровать товары по MIN текущей цене",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()

        # Получаем параметры как строки
        max_price_str = request.GET.get('max_price')
        min_price_str = request.GET.get('min_price')

        # Преобразование и валидация
        try:
            max_price = int(max_price_str) if max_price_str else None
            min_price = int(min_price_str) if min_price_str else None
        except (ValueError, TypeError):
            return Response(
                data={"message": "min_price и max_price должны быть целыми числами"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка логики: оба параметра заданы
        if max_price is not None and min_price is not None:
            if max_price <= min_price:
                return Response(
                    data={"message": "Максимальная цена должна быть больше минимальной"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Фильтрация (max_price/min_price — int или None)
        if max_price is not None:
            products = products.filter(price_current__lte=max_price)
        if min_price is not None:
            products = products.filter(price_current__gte=min_price)

        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


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
