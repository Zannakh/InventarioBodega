from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Categoria, Proveedor, Bodega, Producto, Movimiento
from .serializers import (
    CategoriaSerializer, ProveedorSerializer, BodegaSerializer,
    ProductoSerializer, MovimientoSerializer
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nombre")
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre"]


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by("razon_social")
    serializer_class = ProveedorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["razon_social", "rut", "email", "telefono"]


class BodegaViewSet(viewsets.ModelViewSet):
    queryset = Bodega.objects.all().order_by("nombre")
    serializer_class = BodegaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "ubicacion"]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("categoria", "proveedor").all().order_by("nombre")
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["sku", "nombre"]

    # /productos/<id>/historico/  → LOG de movimientos del producto
    @action(detail=True, methods=["get"], url_path="historico")
    def historico(self, request, pk=None):
        producto = self.get_object()
        movimientos = (
            Movimiento.objects
            .filter(producto=producto)
            .select_related("bodega")
            .order_by("-fecha")
        )
        data = MovimientoSerializer(movimientos, many=True).data
        return Response({
            "producto": f"{producto.sku} - {producto.nombre}",
            "historico": data
        })


class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.select_related("producto", "bodega").all().order_by("-fecha")
    serializer_class = MovimientoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["producto__sku", "producto__nombre", "bodega__nombre", "tipo"]

    # Airbags por si alguna validación del modelo se escapa del serializer
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        try:
            return super().partial_update(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
