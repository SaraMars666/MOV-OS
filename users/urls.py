# users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Página de inicio que redirige a admin o cashier según el rol
    path('admin/', views.admin_dashboard, name='admin_dashboard'),  # Dashboard para admins
    path('cashier/', views.cashier_dashboard, name='cashier_dashboard'),  # Vista para cajeros
    path('profile/', views.profile, name='profile'),  # Perfil del usuario
    path('login/', views.custom_login, name='login'),  # Página de login
    path('logout/', views.custom_logout, name='logout'),  # Página de logout
    path('management/', views.user_management, name='user_management'),  # Gestión de usuarios
    path('management/create/', views.create_user, name='create_user'),  # Crear nuevo usuario
    path('management/edit/<int:user_id>/', views.edit_user, name='edit_user'),  # Editar usuario existente
    path('management/delete/<int:user_id>/', views.delete_user, name='delete_user'),  # Eliminar usuario
]

