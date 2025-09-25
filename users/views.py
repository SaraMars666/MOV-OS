#user/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from auth_app.models import User
from .forms import UserForm  # Asegura que UserForm esté configurado con los campos necesarios


def is_admin(user):
    """Función auxiliar para verificar si un usuario es administrador."""
    return user.is_authenticated and user.is_staff


@login_required
def home(request):
    """Redirige a la vista correcta según el rol del usuario."""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('cashier_dashboard')


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def admin_dashboard(request):
    """Vista del dashboard de administración (solo accesible para admin)."""
    return render(request, 'users/admin_dashboard.html')


@login_required
def cashier_dashboard(request):
    """Vista del modo cajero (todos los usuarios pueden acceder)."""
    return render(request, 'cashier/dashboard.html')


def custom_login(request):
    """Manejo de autenticación personalizada."""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')  # Redirige a `home` para lógica de roles
        else:
            return render(request, 'users/login.html', {'error': 'Credenciales incorrectas'})
    return render(request, 'users/login.html')


@login_required
def profile(request):
    """Vista del perfil del usuario."""
    return render(request, 'users/profile.html', {'user': request.user})


def custom_logout(request):
    """Cerrar sesión y redirigir a login."""
    logout(request)
    return redirect('login')


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def user_management(request):
    """Vista de gestión de usuarios (solo accesible para admin)."""
    users = User.objects.all()
    return render(request, 'users/user_management.html', {'users': users})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def create_user(request):
    """Crear un nuevo usuario (solo accesible para admin)."""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])  # Hasheamos la contraseña
            user.save()
            return redirect('user_management')  # Redirige a gestión de usuarios después de crear
    else:
        form = UserForm()
    return render(request, 'users/create_user.html', {'form': form})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def edit_user(request, user_id):
    """Editar usuario existente (solo accesible para admin)."""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_management')
    else:
        form = UserForm(instance=user)
    return render(request, 'users/edit_user.html', {'form': form, 'user': user})


@user_passes_test(is_admin, login_url='cashier_dashboard')
@login_required
def delete_user(request, user_id):
    """Eliminar usuario (solo accesible para admin)."""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user_management')
    return render(request, 'users/delete_user.html', {'user': user})
    