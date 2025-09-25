#cashier/models.py
from django.conf import settings  # Asegúrate de importar settings
from django.db import models
from products.models import Product
from django.contrib.auth import get_user_model

class Venta(models.Model):
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    tipo_venta = models.CharField(
        max_length=20,
        choices=[('boleta', 'Boleta Electrónica'), ('factura', 'Factura Electrónica')],
        default='boleta'
    )
    forma_pago = models.CharField(
        max_length=20,
<<<<<<< HEAD
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
    
    def __str__(self):
        return f"Venta #{self.id} - Total: ${self.formatted_total}"

    def _format_currency(self, value):
        try:
            # Convierte el número a flotante, sin decimales y con puntos para separar los miles
            return "{:,.0f}".format(float(value)).replace(",", ".")
        except Exception:
            return value

    @property
    def formatted_total(self):
        return self._format_currency(self.total)

    @property
    def formatted_cliente_paga(self):
        return self._format_currency(self.cliente_paga)

    @property
    def formatted_vuelto_entregado(self):
        return self._format_currency(self.vuelto_entregado)
=======
        choices=[('efectivo', 'Efectivo'), ('debito', 'Tarjeta de Débito'), ('credito', 'Tarjeta de Crédito')],
        default='efectivo'
    )

    cliente_paga = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # 💵 Nuevo campo
    vuelto_entregado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Venta #{self.id} - Total: ${self.total}"

>>>>>>> 3e3ff94d0698940333443d5f52b07eeea21d739b


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
<<<<<<< HEAD
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ventadetalles')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

=======
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ventadetalles_cashier')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)


>>>>>>> 3e3ff94d0698940333443d5f52b07eeea21d739b
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

<<<<<<< HEAD
    @property
    def formatted_precio_unitario(self):
        try:
            return "{:,.0f}".format(float(self.precio_unitario)).replace(",", ".")
        except Exception:
            return self.precio_unitario

    @property
    def formatted_subtotal(self):
        try:
            return "{:,.0f}".format(float(self.subtotal)).replace(",", ".")
        except Exception:
            return self.subtotal
=======
>>>>>>> 3e3ff94d0698940333443d5f52b07eeea21d739b


User = get_user_model()

class AperturaCierreCaja(models.Model):
    ESTADO_CAJA = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Cajero Responsable")
    fecha_apertura = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Apertura")
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name="Fecha y Hora de Cierre")
    efectivo_inicial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Efectivo Inicial (Caja Chica)")
    total_ventas_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Total Ventas en Efectivo")
    total_ventas_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Total Ventas con Tarjeta de Crédito")
    total_ventas_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Total Ventas con Tarjeta de Débito")
    estado = models.CharField(max_length=10, choices=ESTADO_CAJA, default='abierta', verbose_name="Estado de la Caja")
    ventas_totales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Ventas Totales"
    )
    vuelto_entregado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, 
        verbose_name="Total Vuelto Entregado"
    )
    efectivo_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Efectivo Final"
    )
<<<<<<< HEAD
    
=======
>>>>>>> 3e3ff94d0698940333443d5f52b07eeea21d739b
    class Meta:
        verbose_name = "Apertura y Cierre de Caja"
        verbose_name_plural = "Aperturas y Cierres de Caja"

    def __str__(self):
        return f"Caja {self.estado.capitalize()} - {self.usuario.username} - {self.fecha_apertura.strftime('%d-%m-%Y %H:%M')}"

