from django.urls import path

from .views import (
    ProductListCreateView,
    ProductDetailView,
    CategoryTreeView,
    ProductRecommendationsView,
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<uuid:pk>/recommendations/', ProductRecommendationsView.as_view(), name='product-recommendations'),
    path('categories/tree/', CategoryTreeView.as_view(), name='category-tree'),
]
