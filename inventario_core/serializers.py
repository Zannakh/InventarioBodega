from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Categoria, Proveedor, Bodega, Producto, Movimiento


# ---------- Básicos ----------
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


# ---------- Producto ----------
class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id", "sku", "nombre", "categoria", "categoria_nombre",
            "proveedor", "proveedor_nombre", "precio", "stock_actual"
        ]

    def validate_sku(self, value):
        """
        Mensaje claro si el SKU ya existe. Si tu modelo ya tiene unique=True,
        esto mejora la respuesta del API en vez de explotar con 500/IntegrityError.
        """
        qs = Producto.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El SKU ya existe.")
        return value


# ---------- Movimiento ----------
class MovimientoSerializer(serializers.ModelSerializer):
    producto_sku = serializers.CharField(source="producto.sku", read_only=True)
    bodega_nombre = serializers.CharField(source="bodega.nombre", read_only=True)

    class Meta:
        model = Movimiento
        fields = [
            "id", "producto", "producto_sku", "bodega", "bodega_nombre",
            "tipo", "cantidad", "fecha", "observacion"
        ]

    # Si usas choices en el modelo, DRF valida solo; esto refuerza mensaje.
    def validate_tipo(self, value):
        validos = {"ENTRADA", "SALIDA", "MERMA"}
        if value not in validos:
            raise serializers.ValidationError("Tipo inválido. Use ENTRADA, SALIDA o MERMA.")
        return value

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser > 0.")
        return value

    def validate(self, attrs):
        """
        Valida stock negativo ANTES de guardar.
        - Creación: evalúa contra stock_actual.
        - Edición: “desaplica” el movimiento previo y evalúa el nuevo.
        Usa tu campo real: stock_actual.
        """
        producto = attrs.get("producto") or getattr(self.instance, "producto", None)
        tipo     = attrs.get("tipo")     or getattr(self.instance, "tipo", None)
        cantidad = attrs.get("cantidad") or getattr(self.instance, "cantidad", None)

        if not producto or not tipo or not cantidad:
            return attrs  # DRF se encarga de requeridos

        stock_eval = producto.stock_actual

        # Si se está editando, revertimos el efecto anterior para evaluar el nuevo
        if self.instance:
            prev = self.instance
            if prev.tipo == "ENTRADA":
                stock_eval -= prev.cantidad
            else:  # SALIDA o MERMA
                stock_eval += prev.cantidad

        # Para salidas/mermas, no permitir quedar negativo
        if tipo in ("SALIDA", "MERMA") and cantidad > stock_eval:
            raise serializers.ValidationError({
                "cantidad": f"No hay stock suficiente (disponible: {stock_eval})."
            })

        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            # traduce errores del modelo a 400 limpio
            raise serializers.ValidationError({"detail": e.messages})

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})
