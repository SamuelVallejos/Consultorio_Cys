from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('historial/', views.historial, name="historial"),
    path('acercade/', views.acercade, name="acercade"),
    path('perfil/', views.perfil_view, name="perfil"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/doctor/', views.doctor_dashboard, name="doctor_dashboard"),
    path('dashboard/paciente/', views.paciente_dashboard, name="paciente_dashboard"),
    path('doctor/add/', views.add_doctor_view, name="add_doctor"),
    path('ia/', views.ia, name="ia"), 
    path('form_cita/', views.form_cita, name="form_cita"), 
    path('informe_doctores/', views.informe_doctores, name='informe_doctores'),
    path('buscar_paciente/', views.buscar_paciente, name='buscar_paciente'),
    path('historial_personal/', views.historial_personal, name='historial_personal'),
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/nuevo/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<str:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<str:pk>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),
    path('pacientes/<str:pk>/informe/', views.informe_paciente, name='informe_paciente'),
    path('pacientes/<str:pk>/crear_informe/', views.crear_informe, name='crear_informe'),  # Nueva ruta para crear informe
    path('paciente_info/<str:rut_paciente>/', views.paciente_info, name='paciente_info'),
    path('ver_calendario/', views.ver_calendario, name='ver_calendario'),
    path('obtener_citas_json/', views.obtener_citas_json, name='obtener_citas_json'),
    path('buscar_doctores/', views.pedir_hora, name='buscar_doctores'),
    path('pedir_hora/', views.pedir_hora, name='pedir_hora'),
    path('seleccionar_doctor/', views.seleccionar_doctor, name='seleccionar_doctor'),
    path('horarios_doctor/<str:doctor_id>/', views.horarios_doctor, name='horarios_doctor'),
    path('informe/<int:pk>/', views.detalle_informe, name='detalle_informe'),
]