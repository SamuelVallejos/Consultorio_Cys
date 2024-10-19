from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('historial/', views.historial, name="historial"),
    path('perfil/', views.perfil_view, name="perfil"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/doctor/', views.doctor_dashboard, name="doctor_dashboard"),
    path('dashboard/paciente/', views.paciente_dashboard, name="paciente_dashboard"),
    path('doctor/add/', views.add_doctor_view, name="add_doctor"),
    path('ia/', views.ia, name="ia"), 
    path('informe_doctores/', views.informe_doctores, name='informe_doctores'),
    path('buscar_paciente/', views.buscar_paciente, name='buscar_paciente'),
    path('historial_personal/', views.historial_personal, name='historial_personal'),
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/nuevo/', views.crear_paciente, name='crear_paciente'),
  path('pacientes/<str:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<str:pk>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),
    path('pacientes/<str:pk>/informe/', views.informe_paciente, name='informe_paciente'),
]