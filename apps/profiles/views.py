from uuid import UUID
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.common.utils import set_dict_attr
from apps.common.permissions import IsOwner
from apps.profiles.serializers import ProfileSerializer, ShippingAddressSerializer
from apps.profiles.models import ShippingAddress, Order, OrderItem
from apps.shop.serializers import OrderSerializer, CheckItemOrderSerializer


tags = ["Profiles"]


class ProfileView(APIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsOwner]


    @extend_schema(
        summary='Получить профиль',
        description="""
            Этот эндпоинт позволяет пользователю получить свой профиль.
        """,
        tags=tags,
    )
    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary='Обновить профиль',
        description="""
            Этот эндпоинт позволяет пользователю обновлять свой профиль.
        """,
        tags=tags,
        request={'multipart/form-data': serializer_class},
    )
    def put(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_dict_attr(user, serializer.validated_data)
        user.save()
        serializer = self.serializer_class(user)
        return Response(data=serializer.data)

    @extend_schema(
        summary='Деактивировать учетную запись',
        description="""
            Этот эндпоинт позволяет пользователю деактивировать свою учетную запись.
        """,
        tags=tags,
    )
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(data={"message": "Учетная запись пользователя деактивирована"})


class ShippingAddressView(APIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        summary='Получение адреса доставки',
        description="""
            Этот эндпоинт возвращает все адреса доставки, связанные с пользователем..
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_addresses = ShippingAddress.objects.filter(user=user)

        serializer = self.serializer_class(shipping_addresses, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary='Создать адрес доставки',
        description="""
            Этот эндпоинт позволяет пользователю создать адрес доставки.
        """,
        tags=tags,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address, _ = ShippingAddress.objects.get_or_create(user=user, **data)
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=201)


class ShippingAddressViewID(APIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsOwner]

    def get_object(self, user, shipping_id):
        try:
            shipping_uuid = UUID(shipping_id)
        except ValueError as exc:
            raise ValidationError({"message": "Неверный формат UUID идентификатора доставки."}) from exc

        shipping_address = ShippingAddress.objects.get_or_none(id=shipping_uuid)
        if shipping_address is None:
            raise NotFound(detail={"message": "Адрес доставки не существует!"}, code=404)
        self.check_object_permissions(self.request, shipping_address)

        return shipping_address

    @extend_schema(
        summary='Идентификатор получения адреса доставки',
        description="""
        Этот эндпоинт возвращает один адрес доставки, связанный с пользователем.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data)

    @extend_schema(
        summary='Обновить идентификатор адреса доставки',
        description="""
        Этот эндпоинт позволяет пользователю обновить свой адрес доставки.
        """,
        tags=tags,
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address = set_dict_attr(shipping_address, data)
        shipping_address.save()
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary='Удалить идентификатор адреса доставки',
        description="""
        Этот эндпоинт позволяет пользователю удалить свой адрес доставки.
        """,
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs['id'])
        shipping_address.delete()
        return Response(data={"message": "Адрес доставки успешно удален"}, status=200)


class OrdersView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        operation_id="orders_view",
        summary="Получение заказов",
        description="""
            Этот эндпоинт возвращает список всех заказов, принадлежащих конкретному пользователю.
        """,
        tags=tags
    )
    def get(self, request):
        user = request.user
        orders = (Order.objects.filter(user=user).select_related("user")
                  .prefetch_related("orderitems", "orderitems__product")
                  .order_by("-created_at"))
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=200)


class OrderItemsView(APIView):
    serializer_class = CheckItemOrderSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        operation_id="order_items_view",
        summary="Заказ товаров",
        description="""
            Этот эндпоинт возвращает список элементов конкретного заказа (товаров внутри заказа).
        """,
        tags=tags,
    )
    def get(self, request, **kwargs):
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order or order.user != request.user:
            return Response(data={"message": "Заказа не существует!"}, status=404)
        order_items = OrderItem.objects.filter(order=order).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=200)
