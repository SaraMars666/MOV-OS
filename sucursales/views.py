from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import SucursalForm
from .models import Sucursal
from products.views import sucursal_products as _sucursal_products_view

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def create_sucursal(request):
    """Vista para crear una nueva sucursal (solo para admin)."""
    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sucursal creada exitosamente.")
            return redirect('sucursales:sucursal_list')
    else:
        form = SucursalForm()
    return render(request, 'sucursales/create_sucursal.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def sucursal_list(request):
    """Vista para listar todas las sucursales (solo para admin)."""
    sucursales = Sucursal.objects.all()
    return render(request, 'sucursales/sucursal_list.html', {'sucursales': sucursales})

@login_required
@user_passes_test(is_admin)
def edit_sucursal(request, pk):
    """Vista para editar una sucursal existente (solo para admin)."""
    sucursal = get_object_or_404(Sucursal, pk=pk)
    form = SucursalForm(request.POST or None, instance=sucursal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Sucursal actualizada exitosamente.")
        return redirect('sucursales:sucursal_list')
    return render(request, 'sucursales/edit_sucursal.html', {'form': form, 'sucursal': sucursal})

@login_required
@user_passes_test(is_admin)
def sucursal_products(request, sucursal_id):
    """Proxy a la vista de listado de productos por sucursal."""
    return _sucursal_products_view(request, sucursal_id)
