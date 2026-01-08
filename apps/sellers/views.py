from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import set_dict_attr
from apps.common.permissions import IsSeller
from apps.profiles.models import Order, OrderItem
from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Product, Category
from apps.shop.serializers import ProductSerializer, CreateProductSerializer, OrderSerializer, \
    CheckItemOrderSerializer



tags = ['Sellers']


class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary='Подайте заявку, чтобы стать продавцом',
        description="""
        Этот эндпоинт позволяет покупателю подать заявку на то, чтобы стать продавцом.
        """,
        tags=tags,
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            user.account_type = 'SELLER'
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=200)
        return Response(data=serializer.errors, status=400)


class SellerProductsView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [IsSeller]

    @extend_schema(
        summary="Получение продуктов продавца",
        description="""
            Этот эндпоинт возвращает все товары от продавца.
            Товары можно фильтровать по названию, размеру или цвету.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={"message": "Доступ запрещен"}, status=403)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Создать продукт",
        description="""
            Этот эндпоинт позволяет продавцу создавать продукт.
        """,
        tags=tags,
        request=CreateProductSerializer,
        responses=ProductSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={"message": "Доступ запрещен"}, status=403)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(data={"message": "Категория не существует!"}, status=404)
            data['category'] = category
            data['seller'] = seller
            new_prod = Product.objects.create(**data)
            serializer = ProductSerializer(new_prod)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    serializer_class = CreateProductSerializer
    permission_classes = [IsSeller]

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        self.check_object_permissions(self.request, product)
        return product

    @extend_schema(
        summary="Обновление продукта продавца",
        description="""
                Этот эндпоинт позволяет продавцу обновит свой продукт.
            """,
        tags=tags,
        responses=ProductSerializer
    )
    def put(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={"message": "Продукт не существует!"}, status=404)
        elif product.seller != request.user.seller:
            return Response(data={"message": "Доступ запрещен"}, status=403)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(data={"message": "Category does not exist!"}, status=404)
            data['category'] = category
            if data['price_current'] != product.price_current:
                data['price_old'] = product.price_current
            product = set_dict_attr(product, data)
            product.save()
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @extend_schema(
        summary="Удаление продукта продавца",
        description="""
                    Этот эндпоинт позволяет продавцу удалит свой продукт.
                """,
        tags=tags
    )
    def delete(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={"message": "Продукт не существует!"}, status=404)
        elif product.seller != request.user.seller:
            return Response(data={"message": "Доступ запрещен"}, status=403)

        product.delete()
        return Response(data={"message": "Товар успешно удален"}, status=200)


class SellerOrdersView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [IsSeller]

    @extend_schema(
        operation_id="seller_orders_view",
        summary="Заказы продавца",
        description="""
            Этот эндпоинт возвращает все заказы для конкретного продавца.
        """,
        tags=tags
    )
    def get(self, request):
        seller = request.user.seller
        orders = (
            Order.objects.filter(orderitems__product__seller=seller)
            .distinct()
            .order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=200)



class SellerOrderItemsView(APIView):
    serializer_class = CheckItemOrderSerializer
    permission_classes = [IsSeller]

    @extend_schema(
        operation_id="seller_order_items_view",
        summary="Заказ товара продавца",
        description="""
            Этот эндпоинт возвращает список элементов заказа (товаров для конкретного заказа), 
            принадлежащего данному продавцу.
        """,
        tags=tags,

    )
    def get(self, request, **kwargs):
        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order:
            return Response(data={"message": "Заказа не существует!"}, status=404)
        order_items = OrderItem.objects.filter(order=order, product__seller=seller)
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=200)
