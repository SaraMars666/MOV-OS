# users/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings  


class Vendedor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)  # Campo para diferenciar roles

    def __str__(self):
        return self.user.username
