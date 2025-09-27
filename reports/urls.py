from django.urls import path
from . import views
from .views import caja_report

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('sales/dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('sales/history/', views.sales_history, name='sales_history'),
    path('sales/<int:sale_id>/', views.sales_report, name='sales_report'),
    path('cash/history/', views.cash_history, name='historial_caja'), 
    path('avanzados/', views.advanced_reports, name='advanced_reports'),
    path('caja/<int:caja_id>/reporte/', caja_report, name='caja_report'),
]
