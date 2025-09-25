# cashier/forms.py
from django import forms
from .models import AperturaCierreCaja

class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = AperturaCierreCaja
        fields = ['efectivo_inicial']  # Cambiamos al nombre correcto del campo
        widgets = {
            'efectivo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese efectivo inicial',
            }),
        }
        labels = {
            'efectivo_inicial': 'Efectivo Inicial (Caja Chica)',
        }
