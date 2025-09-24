#cashier/views.py
from django.urls import path
from . import views
from cashier.views import reporte_venta, cerrar_caja

urlpatterns = [
    path('', views.cashier_dashboard, name='cashier_dashboard'),
    path('abrir-caja/', views.abrir_caja, name='abrir_caja'),
    path('cerrar_caja/', views.cerrar_caja, name='cerrar_caja'),

    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),
    path('ajustar-cantidad/', views.ajustar_cantidad, name='ajustar_cantidad'),
    path('agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('listar-carrito/', views.listar_carrito, name='listar_carrito'),
    path('limpiar-carrito/', views.limpiar_carrito, name='limpiar_carrito'),
    path('detalle-caja/<int:caja_id>/', views.detalle_caja, name='detalle_caja'),
    path('reporte/<int:venta_id>/', views.reporte_venta, name='reporte_venta'),
    path('borrar-historial-caja/', views.delete_all_sales_and_cash_history, name='delete_all_sales_and_cash_history'),


    
]
