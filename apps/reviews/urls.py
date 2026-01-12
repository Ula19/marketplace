from django.urls import path

from .views import ReviewCreateView, ReviewListView, MyReviewsListView, MyReviewDetailView


urlpatterns = [
    path('my/', MyReviewsListView.as_view()),
    path('product/<slug:slug>/', ReviewListView.as_view()),
    path('create/<slug:slug>/', ReviewCreateView.as_view()),
    path('detail/<slug:slug>/', MyReviewDetailView.as_view()),
]
