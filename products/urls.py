#products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('management/', views.product_management, name='product_management'),
    path('create/', views.create_or_edit_product, name='create_product'),
    path('edit/<int:product_id>/', views.create_or_edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),  
    path('products/upload/', views.upload_products, name='upload_products'),
    path('products/template/', views.download_template, name='download_template'),
    path('products/delete-all/', views.delete_all_products, name='delete_all_products'),
    path('exportar/excel/', views.export_products_to_excel, name='export_products_to_excel'),
]
