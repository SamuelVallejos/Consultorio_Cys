from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login  # Importa y renombra la función
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import logout
from .forms import CustomUserCreationForm

def inicio(request):
    return render(request, 'consultorioCys/inicio.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil(request):
    return render(request, 'consultorioCys/perfil.html')

def login_view(request):
    # Renombrada de 'login' a 'login_view' para evitar conflictos
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)  # Usa la función renombrada 'auth_login'
            return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'consultorioCys/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guardar el usuario
            auth_login(request, user)  # Autenticar al usuario después del registro
            return redirect('inicio')  # Redirige a la página de inicio
    else:
        form = CustomUserCreationForm()
    return render(request, 'consultorioCys/register.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('login')