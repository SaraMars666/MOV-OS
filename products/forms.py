from django import forms
from .models import Product
from decimal import Decimal

class ProductForm(forms.ModelForm):
    """
    Formulario simplificado para la gestión de productos.
    """
    class Meta:
        model = Product
        fields = [
            'nombre', 'descripcion', 'producto_id', 'codigo_alternativo',
            'proveedor', 'fecha_ingreso_producto', 'precio_compra', 'precio_venta',
            'cantidad', 'stock', 'codigo_barras', 'permitir_venta_sin_stock'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'producto_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID único del producto'}),
            'codigo_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_ingreso_producto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'permitir_venta_sin_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].label = 'NOMBRE DEL PRODUCTO'
        self.fields['descripcion'].label = 'DESCRIPCIÓN'
        self.fields['producto_id'].label = 'CÓDIGO 1'
        self.fields['codigo_alternativo'].label = 'CÓDIGO 2'
        self.fields['proveedor'].label = 'PROVEEDOR'
        self.fields['fecha_ingreso_producto'].label = 'FECHA DE INGRESO'
        self.fields['precio_compra'].label = 'PRECIO DE COMPRA'
        self.fields['precio_venta'].label = 'PRECIO DE VENTA'
        # ✅ Establecer el valor inicial a True si no es una instancia existente
        if self.instance is None or not self.instance.pk:
            self.fields['permitir_venta_sin_stock'].initial = True

    def clean_producto_id(self):
        """Valida que el producto_id no esté vacío y sea único."""
        producto_id = self.cleaned_data.get('producto_id')
        if not producto_id:
            raise forms.ValidationError("El CÓDIGO 1 no puede estar vacío.")

        qs = Product.objects.filter(producto_id=producto_id)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("El CÓDIGO 1 debe ser único.")
        return producto_id

    def clean(self):
        # La lógica de limpieza y cálculo automático se ha eliminado.
        return super().clean()