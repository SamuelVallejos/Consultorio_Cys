from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from .forms import CustomUserCreationForm, CustomUserEditForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from django.contrib.auth.models import Group

def handle_form_submission(request, form_class, template_name, success_url, instance=None, authenticate_user=False):
    """Utility function to handle form submissions."""
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            # Solo autenticar si se pasa como parámetro
            if authenticate_user:
                auth_login(request, form.get_user()) if instance is None else None
            return redirect(success_url)
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form})

def inicio(request):
    return render(request, 'consultorioCys/inicio.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil_view(request):
    return handle_form_submission(request, CustomUserEditForm, 'consultorioCys/perfil.html', 'perfil', instance=request.user)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'consultorioCys/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Verificar si es doctor
            if form.cleaned_data['is_doctor']:
                # Añadir al grupo "Doctor"
                group = Group.objects.get(name='Doctor')
                user.groups.add(group)
                login(request, user)  # Autenticar automáticamente
                return redirect('doctor_dashboard')
            else:
                # Añadir al grupo "Usuario"
                group = Group.objects.get(name='Usuario')
                user.groups.add(group)
                login(request, user)  # Autenticar automáticamente
                return redirect('usuario_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'consultorioCys/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

# Función auxiliar para verificar si es usuario
def is_usuario(user):
    return user.groups.filter(name='Usuario').exists()

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    # Lógica específica para doctores
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
@user_passes_test(is_usuario)
def usuario_dashboard(request):
    # Lógica específica para usuarios normales
    return render(request, 'consultorioCys/inicio.html')

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

@login_required
@user_passes_test(is_doctor)
def add_doctor_view(request):
    if request.method == 'POST':
        form = AddDoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doctor_dashboard')  # Redirigir a algún lugar después de agregar el doctor
    else:
        form = AddDoctorForm()
    return render(request, 'consultorioCys/add_doctor.html', {'form': form})