from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from users import views

def redirect_to_login(request):
    return redirect('login')  # Redirección a la página de login en `auth_app`

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),  # URLs de autenticación
    path('users/', include('users.urls')),    # URLs para el perfil de usuario
    path('products/', include('products.urls')),  # URLs para productos
    path('cashier/', include('cashier.urls')),  # URLs para ventas
    path('reports/', include('reports.urls')),  # URLs para reportes
    path('', redirect_to_login, name='redirect_to_login'),  # Redirección al login
    path('login/', views.custom_login, name='login'),
]
