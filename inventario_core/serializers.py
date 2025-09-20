from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Categoria, Proveedor, Bodega, Producto, Movimiento


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = "__all__"


class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bodega
        fields = "__all__"


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id", "sku", "nombre", "categoria", "categoria_nombre",
            "proveedor", "proveedor_nombre", "precio", "stock_actual"
        ]


class MovimientoSerializer(serializers.ModelSerializer):
    producto_sku = serializers.CharField(source="producto.sku", read_only=True)
    bodega_nombre = serializers.CharField(source="bodega.nombre", read_only=True)

    class Meta:
        model = Movimiento
        fields = [
            "id", "producto", "producto_sku", "bodega", "bodega_nombre",
            "tipo", "cantidad", "fecha", "observacion"
        ]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser > 0.")
        return value

    def validate(self, attrs):
        """
        Valida stock negativo ANTES de intentar guardar:
        - Para creación: usa stock_actual del producto.
        - Para edición: “desaplica” el movimiento anterior y evalúa el nuevo.
        """
        producto = attrs.get("producto") or getattr(self.instance, "producto", None)
        tipo     = attrs.get("tipo")     or getattr(self.instance, "tipo", None)
        cantidad = attrs.get("cantidad") or getattr(self.instance, "cantidad", None)

        if not producto or not tipo or not cantidad:
            return attrs  # DRF validará faltantes

        stock_eval = producto.stock_actual

        if self.instance:
            # Revertir efecto previo para evaluar el nuevo cambio
            prev = self.instance
            if prev.tipo == "ENTRADA":
                stock_eval -= prev.cantidad
            else:  # SALIDA o MERMA
                stock_eval += prev.cantidad

        if tipo in ("SALIDA", "MERMA") and cantidad > stock_eval:
            raise serializers.ValidationError({
                "cantidad": f"No hay stock suficiente (disponible: {stock_eval})."
            })

        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            # Traduce ValidationError del modelo a error 400 limpio
            raise serializers.ValidationError({"detail": e.messages})

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})
