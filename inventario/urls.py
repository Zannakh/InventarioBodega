from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from inventario_core.views import (
    CategoriaViewSet, ProveedorViewSet, BodegaViewSet,
    ProductoViewSet, MovimientoViewSet
)

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"proveedores", ProveedorViewSet, basename="proveedores")
router.register(r"bodegas", BodegaViewSet, basename="bodegas")
router.register(r"productos", ProductoViewSet, basename="productos")
router.register(r"movimientos", MovimientoViewSet, basename="movimientos")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(router.urls)),
    # Endpoints JWT
    path("auth/jwt/create/", TokenObtainPairView.as_view(), name="jwt_create"),
    path("auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
]
