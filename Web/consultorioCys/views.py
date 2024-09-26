from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login  # Importa y renombra la función
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el usuario en la base de datos
            auth_login(request, user)  # Autentica al usuario automáticamente después del registro
            return redirect('inicio')  # Redirige a la página de inicio
    else:
        form = UserCreationForm()
    return render(request, 'consultorioCys/register.html', {'form': form})
