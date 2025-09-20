from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    razon_social = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)  # puedes validar/formatear después
    email = models.EmailField()
    telefono = models.CharField(max_length=30)

    class Meta:
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class Bodega(models.Model):
    nombre = models.CharField(max_length=120)
    ubicacion = models.CharField(max_length=200)

    class Meta:
        ordering = ["nombre"]
        unique_together = [("nombre", "ubicacion")]

    def __str__(self):
        return f"{self.nombre} - {self.ubicacion}"


class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="productos")
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock_actual = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.sku} - {self.nombre}"


class Movimiento(models.Model):
    ENTRADA, SALIDA, MERMA = "ENTRADA", "SALIDA", "MERMA"
    TIPOS = [(ENTRADA, "Entrada"), (SALIDA, "Salida"), (MERMA, "Merma")]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(default=timezone.now)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tipo} {self.cantidad} de {self.producto} en {self.bodega}"

    def clean(self):
        if self.cantidad == 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Aplica reglas de stock:
           - ENTRADA: suma
           - SALIDA/MERMA: resta (sin negativos)
           Soporta edición de un movimiento (revierte el efecto anterior)."""
        self.clean()

        # Si estamos editando, revertimos el efecto del movimiento previo
        if self.pk:
            prev = Movimiento.objects.select_for_update().get(pk=self.pk)
            prod_prev = Producto.objects.select_for_update().get(pk=prev.producto_id)

            if prev.tipo == self.ENTRADA:
                prod_prev.stock_actual -= prev.cantidad
            else:  # SALIDA o MERMA
                prod_prev.stock_actual += prev.cantidad

            if prod_prev.stock_actual < 0:
                raise ValidationError("Stock negativo al revertir el movimiento previo.")
            prod_prev.save()

        # Aplicar el movimiento actual
        prod = Producto.objects.select_for_update().get(pk=self.producto_id)
        nuevo = prod.stock_actual + self.cantidad if self.tipo == self.ENTRADA else prod.stock_actual - self.cantidad
        if nuevo < 0:
            raise ValidationError("Operación inválida: el stock no puede quedar negativo.")

        prod.stock_actual = nuevo
        prod.save()

        super().save(*args, **kwargs)
