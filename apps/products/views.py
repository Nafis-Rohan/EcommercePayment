from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models import Product
from .serializers import ProductSerializer
from .services import CategoryTreeService


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class CategoryTreeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(CategoryTreeService.get_tree())


class ProductRecommendationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")

        category_ids = CategoryTreeService.get_category_and_descendant_ids(product.category_id)

        recommendations = (
            Product.objects.filter(category_id__in=category_ids)
            .exclude(id=product.id)
            .order_by('-created_at')[:10]
        )
        return Response(ProductSerializer(recommendations, many=True).data)
