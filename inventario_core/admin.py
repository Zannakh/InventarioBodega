from django.contrib import admin
from .models import Categoria, Proveedor, Bodega, Producto, Movimiento
from .forms import MovimientoAdminForm

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("sku", "nombre", "categoria", "proveedor", "precio", "stock_actual")
    search_fields = ("sku", "nombre")
    list_filter = ("categoria", "proveedor")

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    form = MovimientoAdminForm
    list_display = ("producto", "bodega", "tipo", "cantidad", "fecha")
    list_filter = ("tipo", "bodega")
    search_fields = ("producto__sku", "producto__nombre")

admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Bodega)
