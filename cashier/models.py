#cashier/models.py
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from products.models import Product
from sucursales.models import Sucursal
from django.contrib.auth import get_user_model

User = get_user_model()

# Modelo de Venta
class Venta(models.Model):
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='ventas', blank=True, null=True)
    caja = models.ForeignKey('AperturaCierreCaja', on_delete=models.SET_NULL, related_name='ventas', blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    tipo_venta = models.CharField(
        max_length=20,
        choices=[('boleta', 'Boleta Electrónica'), ('factura', 'Factura Electrónica')],
        default='boleta'
    )
    forma_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('debito', 'Tarjeta de Débito'),
            ('credito', 'Tarjeta de Crédito'),
            ('transferencia', 'Transferencia')
        ],
        default='efectivo'
    )
    
    cliente_paga = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vuelto_entregado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    numero_transaccion = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Número de Transacción"
    )
    banco = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Banco"
    )
    
    def __str__(self):
        return f"Venta #{self.id} - Total: {self.total}"

# Modelo para el detalle de la venta
class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ventadetalles')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

# Modelo de Apertura y Cierre de Caja (actualizado)
class AperturaCierreCaja(models.Model):
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name='Vendedor'
    )
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    efectivo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, default='abierta')  # valores: 'abierta' o 'cerrada'
    apertura = models.DateTimeField(auto_now_add=True)
    cierre = models.DateTimeField(null=True, blank=True)
    # Campos adicionales para el cierre de caja agregados
    ventas_totales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vuelto_entregado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    efectivo_final = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Caja {self.id} - {self.vendedor.username} - {self.estado}"

    class Meta:
        constraints = [
            # Garantiza que sólo exista una caja 'abierta' por sucursal a la vez
            models.UniqueConstraint(
                fields=['sucursal'],
                condition=Q(estado='abierta'),
                name='unique_open_caja_per_sucursal'
            )
        ]

