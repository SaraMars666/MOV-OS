from django.db import models

class Sucursal(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=500, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nombre

