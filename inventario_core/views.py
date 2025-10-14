from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Categoria, Proveedor, Bodega, Producto, Movimiento
from .serializers import (
    CategoriaSerializer, ProveedorSerializer, BodegaSerializer,
    ProductoSerializer, MovimientoSerializer
)
from .permissions import RolCompositePermission


# ───────────────────────────────────────────────────────────────────
# Utilidades internas para stock
# ───────────────────────────────────────────────────────────────────
def _aplicar_delta_stock(producto: Producto, tipo: str, cantidad: int) -> None:
    """
    Aplica delta sobre producto.stock_actual según tipo:
      ENTRADA: +cantidad
      SALIDA / MERMA: -cantidad
    """
    if tipo == "ENTRADA":
        producto.stock_actual = (producto.stock_actual or 0) + cantidad
    else:  # SALIDA o MERMA
        producto.stock_actual = (producto.stock_actual or 0) - cantidad
    producto.save(update_fields=["stock_actual"])


def _revertir_movimiento(producto: Producto, tipo: str, cantidad: int) -> None:
    """
    Revierte el efecto del movimiento anterior:
      Si el anterior fue ENTRADA, ahora resta; si fue SALIDA/MERMA, ahora suma.
    """
    if tipo == "ENTRADA":
        producto.stock_actual = (producto.stock_actual or 0) - cantidad
    else:  # SALIDA o MERMA
        producto.stock_actual = (producto.stock_actual or 0) + cantidad
    producto.save(update_fields=["stock_actual"])


# ───────────────────────────────────────────────────────────────────
# BaseViewSet con permisos globales
# ───────────────────────────────────────────────────────────────────
class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RolCompositePermission]


# ───────────────────────────────────────────────────────────────────
# Catálogo
# ───────────────────────────────────────────────────────────────────
class CategoriaViewSet(BaseViewSet):
    queryset = Categoria.objects.all().order_by("nombre")
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre"]
    ordering_fields = ["nombre"]


class ProveedorViewSet(BaseViewSet):
    queryset = Proveedor.objects.all().order_by("razon_social")
    serializer_class = ProveedorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["razon_social", "rut", "email", "telefono"]
    ordering_fields = ["razon_social"]


class BodegaViewSet(BaseViewSet):
    queryset = Bodega.objects.all().order_by("nombre")
    serializer_class = BodegaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "ubicacion"]
    ordering_fields = ["nombre"]


class ProductoViewSet(BaseViewSet):
    queryset = (
        Producto.objects.select_related("categoria", "proveedor")
        .all()
        .order_by("nombre")
    )
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["sku", "nombre", "categoria__nombre", "proveedor__razon_social"]
    ordering_fields = ["nombre", "stock_actual", "precio"]

    @action(detail=False, methods=["get"], url_path="bajo_stock")
    def bajo_stock(self, request):
        """
        /productos/bajo_stock/?umbral=5
        """
        try:
            umbral = int(request.query_params.get("umbral", 5))
        except ValueError:
            return Response({"detail": "umbral debe ser entero."}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(stock_actual__lt=umbral)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=True, methods=["get"], url_path="historico")
    def historico(self, request, pk=None):
        """
        /productos/<id>/historico/
        """
        producto = self.get_object()
        movimientos = (
            Movimiento.objects
            .filter(producto=producto)
            .select_related("bodega")
            .order_by("-fecha", "-id")
        )
        data = MovimientoSerializer(movimientos, many=True).data
        return Response({
            "producto": f"{producto.sku} - {producto.nombre}",
            "historico": data
        })


# ───────────────────────────────────────────────────────────────────
# Movimientos (ajustan stock_actual)
# ───────────────────────────────────────────────────────────────────
class MovimientoViewSet(BaseViewSet):
    queryset = (
        Movimiento.objects.select_related("producto", "bodega")
        .all()
        .order_by("-fecha", "-id")
    )
    serializer_class = MovimientoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["producto__sku", "producto__nombre", "bodega__nombre", "tipo", "observacion"]
    ordering_fields = ["fecha", "id", "cantidad"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crea movimiento y aplica delta al stock_actual.
        """
        try:
            response = super().create(request, *args, **kwargs)
            movimiento = Movimiento.objects.select_related("producto").get(pk=response.data["id"])
            _aplicar_delta_stock(movimiento.producto, movimiento.tipo, movimiento.cantidad)
            return response
        except DjangoValidationError as e:
            transaction.set_rollback(True)
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Edita movimiento:
        1) Revierte el movimiento previo
        2) Guarda cambios
        3) Aplica el nuevo movimiento
        """
        instance = self.get_object()
        try:
            # 1) revertir efecto previo
            producto_prev = instance.producto
            _revertir_movimiento(producto_prev, instance.tipo, instance.cantidad)

            # 2) actualizar
            response = super().update(request, *args, **kwargs)

            # 3) aplicar efecto nuevo
            movimiento = self.get_object()  # recargar
            _aplicar_delta_stock(movimiento.producto, movimiento.tipo, movimiento.cantidad)
            return response
        except DjangoValidationError as e:
            transaction.set_rollback(True)
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """
        Igual que update pero parcial (PATCH).
        """
        instance = self.get_object()
        try:
            producto_prev = instance.producto
            _revertir_movimiento(producto_prev, instance.tipo, instance.cantidad)

            response = super().partial_update(request, *args, **kwargs)

            movimiento = self.get_object()
            _aplicar_delta_stock(movimiento.producto, movimiento.tipo, movimiento.cantidad)
            return response
        except DjangoValidationError as e:
            transaction.set_rollback(True)
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Elimina movimiento revirtiendo su efecto en stock_actual.
        """
        instance = self.get_object()
        try:
            producto = instance.producto
            _revertir_movimiento(producto, instance.tipo, instance.cantidad)
            return super().destroy(request, *args, **kwargs)
        except DjangoValidationError as e:
            transaction.set_rollback(True)
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
