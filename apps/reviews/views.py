from django.db.models import Avg, Count
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from .serializers import ReviewCreateSerializer
from .models import Review
from ..common.permissions import IsSeller, IsOwner
from ..common.utils import set_dict_attr
from ..profiles.models import Order
from ..shop.models import Product


tags = ['Reviews']

class ReviewCreateView(APIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Создать отзыв',
        description='Этот эндпоинт создает отзыв об определенном товаре',
        tags=tags
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=kwargs["slug"])
        if not product:
            return Response({"message": "Нет продукта с таким slug"}, status=status.HTTP_404_NOT_FOUND)

        get_review = Review.objects.get_or_none(user=user, product=product)
        if get_review:
            raise ValidationError('Вы уже оставляли отзыв на этот товар')

        order = Review.objects.create(user=user, product=product, rating=data['rating'], text=data['text'])
        serializer = ReviewCreateSerializer(order)
        return Response(serializer.data)


class ReviewListView(APIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Все отзывы товара',
        description='Этот эндпоинт возвращает все отзывы определенного товара (продукта)',
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=kwargs["slug"])
        if not product:
            return Response({"message": "Нет продукта с таким slug"}, status=status.HTTP_404_NOT_FOUND)
        reviews = Review.objects.filter(product=product)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data)


class MyReviewsListView(APIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        summary='Все Мои отзывы',
        description='Этот эндпоинт возвращает все отзывы определенного юзера',
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        reviews = Review.objects.filter(user=user)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data)


class MyReviewDetailView(APIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsOwner]

    def get_object(self, user, slug):
        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=slug)
        if product is None:
            raise NotFound({"message": "Нет продукта с таким slug"}, code=status.HTTP_404_NOT_FOUND)

        queryset = Review.objects.get_or_none(user=user, product=product)
        if queryset is None:
            raise NotFound({"message": "Нет отзыва у этого пользователь на этот товар"},
                            code=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(self.request, queryset)

        return queryset

    @extend_schema(
        summary='Получить отзыв',
        description='Этот эндпоинт позволяет юзеру получить свой отзыв',
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        review = self.get_object(user, kwargs['slug'])
        serializer = self.serializer_class(review)
        return Response(serializer.data)

    @extend_schema(
        summary='Изменить отзыв',
        description='Этот эндпоинт позволяет юзеру изменить свой отзыв',
        tags=tags
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        review = self.get_object(user, kwargs['slug'])
        serializer = self.serializer_class(review, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        review = set_dict_attr(review, data)
        review.save()
        serializer = self.serializer_class(review)
        return Response(serializer.data)

    @extend_schema(
        summary='Удалить отзыв',
        description='Этот эндпоинт позволяет юзеру удалить свой отзыв (hard_delete)',
        tags=tags,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                }
            }
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        review = self.get_object(user, kwargs['slug'])
        review.hard_delete()
        return Response(data={"message": "Отзыв успешно удален"}, status=200)
