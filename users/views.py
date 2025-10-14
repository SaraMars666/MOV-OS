#user/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from .forms import UserForm
from .models import Vendedor
from django.contrib.auth import get_user_model, authenticate, login, logout
from cashier.models import AperturaCierreCaja
User = get_user_model()  # Importa el modelo de usuario personalizado


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
def home(request):
    # Redirige según el rol
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('cashier_dashboard')


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def admin_dashboard(request):
    return render(request, 'users/admin_dashboard.html')


## Nota: cashier_dashboard es provisto por la app 'cashier'.


def custom_login(request):
    # Si ya está autenticado y vuelve a /login, redirigir según rol/estado de caja
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        # Usuario no admin: enviar al cajero si tiene caja abierta, si no a abrir caja
        tiene_caja = AperturaCierreCaja.objects.filter(vendedor=request.user, estado='abierta').exists()
        return redirect('cashier_dashboard' if tiene_caja else 'abrir_caja')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Redirigir inmediatamente según rol y estado de caja
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            tiene_caja = AperturaCierreCaja.objects.filter(vendedor=user, estado='abierta').exists()
            return redirect('cashier_dashboard' if tiene_caja else 'abrir_caja')
        else:
            messages.error(request, "Credenciales incorrectas.")
            return render(request, 'users/login.html')
    return render(request, 'users/login.html')


@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})


from django.contrib.auth import logout
from django.contrib import messages

def logout_view(request):
    logout(request)
    # Consumir (vaciar) los mensajes
    list(messages.get_messages(request))
    return redirect('login')


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def user_management(request):
    # Si usas User directamente, lista los usuarios; si usas la extensión, quizá quieras listar Vendedor
    users = User.objects.all()
    # Debug: imprime la cantidad de usuarios encontrados
    print("Usuarios encontrados:", users.count())
    return render(request, 'users/user_management.html', {'users': users})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def create_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear usuario básico usando el modelo personalizado
                    username = form.cleaned_data['username']
                    email = form.cleaned_data['email']
                    password = form.cleaned_data['password']
                    is_superuser = form.cleaned_data.get('is_superuser', False)
                    user = User(
                        username=username, 
                        email=email, 
                        is_superuser=is_superuser, 
                        is_staff=is_superuser
                    )
                    user.set_password(password)
                    user.save()
                    # Crear el objeto Vendedor asociado pasando is_admin
                    vendedor = Vendedor.objects.create(user=user, is_admin=is_superuser)
                    sucursales = form.cleaned_data.get('sucursales_autorizadas')
                    if sucursales:
                        vendedor.sucursales_autorizadas.set([s.pk for s in sucursales])
                messages.success(request, "Usuario creado exitosamente.")
                return redirect("user_management")
            except Exception as e:
                print("Error al crear usuario:", e)
                messages.error(request, f"Error al crear el usuario: {e}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = UserForm()
    return render(request, 'users/create_user.html', {'form': form})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    vendedor_obj = Vendedor.objects.filter(user=user_obj).first()
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user_obj.email = form.cleaned_data['email']
                    user_obj.is_superuser = form.cleaned_data.get('is_superuser', False)
                    user_obj.is_staff = form.cleaned_data.get('is_superuser', False)
                    
                    # Actualización de contraseña: si se ingresó un valor para password, 
                    # se actualiza usando set_password()
                    new_password = form.cleaned_data.get('password')
                    if new_password:
                        user_obj.set_password(new_password)
                    
                    user_obj.save()
                    
                    if vendedor_obj:
                        sucursales = form.cleaned_data.get("sucursales_autorizadas")
                        if sucursales:
                            vendedor_obj.sucursales_autorizadas.set([s.pk for s in sucursales])
                        else:
                            vendedor_obj.sucursales_autorizadas.clear()
                messages.success(request, "Usuario actualizado exitosamente.")
                return redirect("user_management")
            except Exception as e:
                messages.error(request, f"Error al actualizar el usuario: {e}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = UserForm(instance=user_obj)
    return render(request, 'users/edit_user.html', {'form': form, 'user': user_obj})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, "Usuario eliminado correctamente.")
        return redirect('user_management')
    return render(request, 'users/delete_user.html', {'user': user_obj})
