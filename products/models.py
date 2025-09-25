from django.db import models
from decimal import Decimal

class Product(models.Model):
    """
    Modelo simplificado para un producto.
    """
    # Campos solicitados
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Producto", blank=True, null=True)
    descripcion = models.TextField(verbose_name="Descripción", blank=True, null=True)
    producto_id = models.CharField(max_length=255, unique=True, verbose_name="Código 1")
    codigo_alternativo = models.CharField(max_length=255, verbose_name="Código 2", blank=True, null=True)
    proveedor = models.CharField(max_length=255, verbose_name="Proveedor", blank=True, null=True)
    fecha_ingreso_producto = models.DateField(verbose_name="Fecha de Ingreso", blank=True, null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra", default=Decimal('0.00'))
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta", default=Decimal('0.00'))
    
    # Campos adicionales que pueden ser útiles
    cantidad = models.IntegerField(verbose_name="Cantidad", default=0)
    stock = models.IntegerField(verbose_name="Stock", default=0)
    codigo_barras = models.CharField(max_length=255, verbose_name="Código de Barras", blank=True, null=True)
    permitir_venta_sin_stock = models.BooleanField(default=True, verbose_name="Permitir Venta sin Stock")

    def __str__(self):
        return self.nombre if self.nombre else self.producto_id or f"Producto sin nombre ({self.pk})"

<<<<<<< HEAD
    def _format_currency(self, value):
        try:
            # Formatea sin decimales y usa el punto para separar miles
            return "{:,.0f}".format(float(value)).replace(",", ".")
        except Exception:
            return value

    @property
    def formatted_precio_compra(self):
        return self._format_currency(self.precio_compra)

    @property
    def formatted_precio_venta(self):
        return self._format_currency(self.precio_venta)

=======
>>>>>>> 3e3ff94d0698940333443d5f52b07eeea21d739b
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"