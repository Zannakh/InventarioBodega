from django import forms
from .models import Movimiento, Producto

class MovimientoAdminForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        tipo     = cleaned.get("tipo")
        cantidad = cleaned.get("cantidad")

        if not producto or not tipo or not cantidad:
            return cleaned

        # Stock “base” para evaluar
        stock_eval = producto.stock_actual

        # Si es edición, revertimos el efecto del movimiento previo
        if self.instance and self.instance.pk:
            prev = Movimiento.objects.get(pk=self.instance.pk)
            if prev.tipo == Movimiento.ENTRADA:
                stock_eval -= prev.cantidad
            else:  # SALIDA o MERMA
                stock_eval += prev.cantidad

        # Regla: no permitir negativos
        if tipo in (Movimiento.SALIDA, Movimiento.MERMA) and cantidad > stock_eval:
            raise forms.ValidationError(
                f"No hay stock suficiente para la operación. Disponible: {stock_eval}."
            )

        return cleaned
