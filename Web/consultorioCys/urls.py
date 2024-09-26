from django.urls import path
from .views import inicio, perfil, historial, register_view, login_view,logout_view

urlpatterns = [
    path('',inicio,name="inicio"),
    path('historial/',historial,name="historial"),
    path('perfil/',perfil,name="perfil"),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
     path('logout/', logout_view, name='logout'),
]