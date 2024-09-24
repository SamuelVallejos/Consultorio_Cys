from django.shortcuts import render
from django.http import HttpResponse

def inicio(request):
    return render(request, 'consultorioCys/inicio.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil(request):
    return render(request, 'consultorioCys/perfil.html')

# Create your views here.
