from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.report_dashboard, name='report_dashboard'),
    path('sales/dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('sales/history/', views.sales_history, name='sales_history'),
    path('sales/<int:sale_id>/reporte/', views.sales_report, name='sales_report'),
    path('cash/history/', views.cash_history, name='historial_caja'),
    path('caja/<int:caja_id>/reporte/', views.caja_report, name='caja_report'),
    path('advanced/', views.advanced_reports, name='advanced_reports'),
    path('advanced/export/rentabilidad.csv', views.export_rentabilidad_csv, name='export_rentabilidad_csv'),
    path('advanced/export/ranking_cajeros.csv', views.export_ranking_cajeros_csv, name='export_ranking_cajeros_csv'),
    path('advanced/export/serie_diaria.csv', views.export_daily_series_csv, name='export_daily_series_csv'),
    path('advanced/export/comparacion_sucursal.csv', views.export_branch_comparison_csv, name='export_branch_comparison_csv'),
    path('advanced/data/', views.advanced_reports_data, name='advanced_reports_data'),
    path('limpiar_historial/', views.limpiar_historial_caja, name='limpiar_historial_caja'),
    path('limpiar_historial_ventas/', views.limpiar_historial_ventas, name='limpiar_historial_ventas'),
]
