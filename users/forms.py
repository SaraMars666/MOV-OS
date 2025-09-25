# users/forms.py

from django import forms
from auth_app.models import User

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_superuser']  # Añade los campos necesarios
        widgets = {
            'password': forms.PasswordInput(),  # Hace que el campo de contraseña sea un input de tipo password
        }
