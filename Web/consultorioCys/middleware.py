from django.utils.timezone import now
from .models import Suscripcion, Paciente

class ValidarSuscripcionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                paciente = Paciente.objects.get(usuario=request.user)
                suscripcion = Suscripcion.objects.filter(paciente=paciente, fecha_fin__gte=now()).last()
                if not suscripcion:
                    request.no_tiene_suscripcion = True
                else:
                    request.no_tiene_suscripcion = False
            except Paciente.DoesNotExist:
                request.no_tiene_suscripcion = True

        response = self.get_response(request)
        return response