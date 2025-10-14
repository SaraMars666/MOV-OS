from django.contrib.auth.models import AbstractUser
from django.db import models
from reports.models import Sucursal

class User(AbstractUser):
    """
    Modelo de usuario personalizado.
    Los usuarios no administradores deben tener asignadas las sucursales en las que pueden abrir caja.
    Los administradores (is_staff o is_superuser) no necesitan esta asignación.
    """
    is_admin = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=True)
    sucursales_autorizadas = models.ManyToManyField(
        Sucursal,
        blank=True,
        related_name='usuarios_autorizados',
        help_text="Sucursales en las que el usuario puede abrir cajas (solo para usuarios no administradores)."
    )

    def __str__(self):
        return f"{self.username} ({'Admin' if self.is_admin else 'Empleado'})"

    def puede_abrir_caja_en(self, sucursal):
        """
        Devuelve True si el usuario puede abrir caja en la sucursal dada.
        Los administradores pueden abrir caja en cualquier sucursal.
        Los demás deben estar autorizados explícitamente.
        """
        if self.is_staff or self.is_superuser:
            return True
        return self.sucursales_autorizadas.filter(id=sucursal.id).exists()
