from django.urls import path
from .views import inicio, perfil, historial

urlpatterns = [
    path('',inicio,name="inicio"),
    path('historial/',historial,name="historial"),
    path('perfil/',perfil,name="perfil"),
]