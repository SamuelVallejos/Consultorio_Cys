from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('historial/', views.historial, name="historial"),
    path('perfil/', views.perfil_view, name="perfil"),
    path('register/', views.register_view, name="register"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/doctor/', views.doctor_dashboard, name="doctor_dashboard"),
    path('dashboard/usuario/', views.usuario_dashboard, name="usuario_dashboard"),
    path('doctor/add/', views.add_doctor_view, name="add_doctor"),
    path('ia/', views.ia, name="ia"),
]
