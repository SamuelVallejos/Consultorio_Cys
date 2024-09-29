from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from .forms import CustomUserCreationForm, CustomUserEditForm

def inicio(request):
    return render(request, 'consultorioCys/inicio.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil_view(request):
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=request.user) 
        if form.is_valid():
            form.save() 
            return redirect('perfil')  
    else:
        form = CustomUserEditForm(instance=request.user) 
    return render(request, 'consultorioCys/perfil.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'consultorioCys/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('inicio')
    else:
        form = CustomUserCreationForm()
    return render(request, 'consultorioCys/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
