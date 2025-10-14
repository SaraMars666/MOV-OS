from django.urls import path
from . import views

app_name = 'sucursales'

urlpatterns = [
    path('', views.sucursal_list, name='sucursal_list'),
    path('create/', views.create_sucursal, name='create_sucursal'),
    path('edit/<int:pk>/', views.edit_sucursal, name='edit_sucursal'),
    path('<int:sucursal_id>/productos/', views.sucursal_products, name='sucursal_products'),
]