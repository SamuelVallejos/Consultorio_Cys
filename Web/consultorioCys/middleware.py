# consultorioCys/middleware.py

from django.shortcuts import redirect
from django.utils.timezone import now
from .models import Suscripcion

class ValidarSuscripcionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            suscripcion = Suscripcion.objects.filter(usuario=request.user).last()
            if not suscripcion or suscripcion.fecha_fin < now():
                return redirect('renovar_suscripcion')
        return self.get_response(request)
