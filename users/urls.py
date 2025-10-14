# users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('management/', views.user_management, name='user_management'),
    path('management/create/', views.create_user, name='create_user'),
    path('management/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('management/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]

