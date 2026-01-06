from django.urls import path

from apps.sellers.views import SellersView, SellerProductsView, SellerProductView

urlpatterns = [
    path('', SellersView.as_view()),
    path("products/", SellerProductsView.as_view()),
    path('product/<str:slug>/', SellerProductView.as_view()),
]
