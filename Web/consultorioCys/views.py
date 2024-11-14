from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from .models import Doctor, Paciente, Informe, Usuario, Clinica, SedeClinica, DoctorClinica, DisponibilidadDoctor
from django.contrib.auth.models import Group, User
from .forms import RUTAuthenticationForm
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.http import JsonResponse
from .models import Paciente, Informe, Cita
from .forms import PacienteForm, CitaForm, InformeForm
from django.urls import reverse
from django.utils import timezone
import datetime
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model

def handle_form_submission(request, form_class, template_name, success_url, instance=None, authenticate_user=False):
    """Utility function to handle form submissions."""
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            # Solo autenticar si se pasa como parámetro
            if authenticate_user:
                auth_login(request, form.get_user()) if instance is None else None
            return redirect(success_url)
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form})

def horarios_doctor(request, doctor_id):
    # Aquí puedes implementar la lógica para mostrar los horarios del doctor.
    doctor = Doctor.objects.get(id=doctor_id)
    horarios = doctor.horarios_set.all()  # Ajusta esto según el modelo de horarios que tengas
    return render(request, 'horarios_doctor.html', {'doctor': doctor, 'horarios': horarios})

@login_required
def inicio(request):
    message = request.GET.get('message')
    print(f"Usuario autenticado: {request.user.is_authenticated}")

    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=request.user)

    # Verificar si el usuario ya tiene una cita confirmada
    cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True).first()

    # Pasar la cita existente al contexto si existe
    return render(request, 'consultorioCys/inicio.html', {
        'message': message,
        'cita_existente': cita_existente
    })

User = get_user_model()

def cambiar_clave(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if new_password == confirm_password:
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Tu contraseña ha sido cambiada exitosamente.")
                return redirect("login")  # Redirige al login después de cambiar la contraseña
            else:
                messages.error(request, "Las contraseñas no coinciden.")
        return render(request, "cambiar_clave.html", {"validlink": True})
    else:
        messages.error(request, "El enlace de restablecimiento no es válido o ha expirado.")
        return render(request, "cambiar_clave.html", {"validlink": False})

def restablecer_clave(request):
    if request.method == "POST":
        email = request.POST.get("email")
        users = Usuario.objects.filter(email=email)
        if users.exists():
            user = users.first()
            subject = "Restablecimiento de contraseña"
            email_template_name = "mensaje_cambio_clave.txt"
            context = {
                "email": user.email,
                "domain": "localhost:8000",  # Cambia esto a tu dominio en producción
                "site_name": "Tu Sitio",
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
                "protocol": "http",  # Cambia a "https" si usas SSL en producción
}
            email_content = render_to_string(email_template_name, context)
            send_mail(subject, email_content, settings.DEFAULT_FROM_EMAIL, [user.email])

            messages.success(request, f"Se ha enviado un mensaje a tu correo {user.email}")
            return redirect("restablecer_clave")
        else:
            messages.error(request, "No se encontró un usuario con ese correo.")
            return redirect("restablecer_clave")
    return render(request, "restablecer_clave.html")

def acercade(request):
    return render(request, 'consultorioCys/acercade.html')

def historial_personal(request):
    usuario = request.user

    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=usuario)

    # Obtener todos los informes del paciente
    informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')

    # Obtener el informe más reciente (opcional, si se necesita para destacar)
    informe_reciente = informes.first() if informes.exists() else None

    # Obtener las citas futuras del paciente
    citas = Cita.objects.filter(
        paciente=paciente,
        fecha_cita__gte=timezone.now().date()
    ).order_by('fecha_cita', 'hora_cita')

    # Obtener el doctor, clínica y sede del informe más reciente
    doctor = informe_reciente.doctor if informe_reciente else None
    clinica = informe_reciente.clinica if informe_reciente else None
    sede = informe_reciente.sede if informe_reciente else None

    context = {
        'paciente': paciente,
        'informes': informes,  # Todos los informes del paciente
        'informe_reciente': informe_reciente,  # Informe más reciente
        'doctor': doctor,
        'clinica': clinica,
        'sede': sede,
        'citas': citas,
    }
    return render(request, 'consultorioCys/historial_personal.html', context)

def detalle_informe(request, pk):
    # Obtener el informe por su ID
    informe = get_object_or_404(Informe, pk=pk)

    return render(request, 'consultorioCys/detalle_informe.html', {'informe': informe})

#AQUI TERMINA EL historial_personal

def historial(request):
    return render(request, 'consultorioCys/historial.html')

@login_required
def resumen_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, "consultorioCys/resumen_cita.html", {"cita": cita})

@login_required
def agendar_cita(request):
    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        hora_cita = request.POST.get("hora_cita")
        fecha_cita = request.POST.get("fecha_cita")
        paciente = request.user.paciente  # Asegúrate de que el usuario tenga un perfil de paciente

        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Crea la cita con la información recibida
        nueva_cita = Cita.objects.create(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha_cita,
            hora_cita=hora_cita,
            motivo_consulta=request.POST.get("motivo_consulta", ""),
            confirmado=True
        )

        # Redirige a la página de resumen con el ID de la cita
        return redirect("resumen_cita", cita_id=nueva_cita.id)
    else:
        return redirect("pedir_hora")
    

@login_required
def confirmacion_cita(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        # Verificar que los datos requeridos existen
        if not doctor_id or not fecha or not hora:
            return render(request, 'confirmacion_cita.html', {
                'error': 'Faltan datos necesarios para la confirmación de la cita.'
            })

        # Obtener el doctor y su información
        doctor = get_object_or_404(Doctor, rut_doctor=doctor_id)
        
        # Obtener al paciente desde el usuario autenticado
        paciente = get_object_or_404(Paciente, usuario=request.user)
        
        # Convertir la hora al formato HH:MM
        try:
            hora_obj = datetime.datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return render(request, 'confirmacion_cita.html', {
                'error': f'El formato de la hora recibido ({hora}) no es válido. Debe estar en el formato HH:MM.'
            })

        # Crear la cita y guardarla en la base de datos
        cita = Cita(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha,
            hora_cita=hora_obj,
            confirmado=True
        )
        cita.save()

        # Obtener la sede asociada al doctor
        doctor_clinica = DoctorClinica.objects.filter(doctor=doctor).first()
        sede = doctor_clinica.sede if doctor_clinica else None

        # Preparar contexto con la información de la cita, incluyendo la ubicación
        context = {
            'doctor': doctor,
            'fecha': fecha,
            'hora': hora_obj.strftime("%H:%M"),
            'especialidad': doctor.especialidad_doctor,
            'ubicacion': f"{sede.clinica.nombre_clinica} - {sede.comuna_sede}, {sede.region_sede}" if sede else "Ubicación no disponible"
        }

        return render(request, 'confirmacion_cita.html', context)
    
    elif request.method == 'GET':
        # Verificar si se está solicitando ver una cita existente
        cita_id = request.GET.get('cita_id')
        if cita_id:
            # Obtener la cita existente
            cita = get_object_or_404(Cita, id=cita_id, paciente__usuario=request.user)
            doctor = cita.doctor
            sede = DoctorClinica.objects.filter(doctor=doctor).first().sede

            context = {
                'doctor': doctor,
                'fecha': cita.fecha_cita,
                'hora': cita.hora_cita.strftime("%H:%M"),
                'especialidad': doctor.especialidad_doctor,
                'ubicacion': f"{sede.clinica.nombre_clinica} - {sede.comuna_sede}, {sede.region_sede}" if sede else "Ubicación no disponible"
            }
            return render(request, 'confirmacion_cita.html', context)
        else:
            return render(request, 'confirmacion_cita.html', {
                'error': 'No se ha especificado ninguna cita para mostrar.'
            })
    
    else:
        return render(request, 'confirmacion_cita.html', {
            'error': 'Método de solicitud no válido.'
        })
    
@login_required
def finalizar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    # Verifica que el usuario sea el doctor de la cita o tenga permisos especiales
    if request.user != cita.doctor.usuario:
        return render(request, 'error.html', {'error': 'No tienes permiso para finalizar esta cita.'})

    # Marcar la cita como finalizada
    cita.finalizada = True
    cita.save()

    # Reactivar la disponibilidad de la hora del doctor
    DisponibilidadDoctor.objects.filter(
        doctor=cita.doctor, fecha=cita.fecha_cita, hora=cita.hora_cita
    ).update(disponible=True)

    return render(request, 'cita_finalizada.html', {'cita': cita})
    
@login_required
def seleccionar_doctor(request):
    especialidad_seleccionada = request.GET.get('especialidad')
    fecha = request.GET.get('fecha')

    # Obtener la lista de doctores de la especialidad seleccionada
    doctores = Doctor.objects.filter(especialidad_doctor=especialidad_seleccionada)
    
    # Crear una lista para almacenar doctores junto con sus horas disponibles
    doctores_con_horarios = []
    for doctor in doctores:
        # Filtrar horas disponibles del doctor en la fecha seleccionada
        horas_disponibles = DisponibilidadDoctor.objects.filter(
            doctor=doctor,
            fecha=fecha,
            disponible=True  # Asegúrate de que sea una hora disponible
        ).values_list('hora', flat=True)
        
        doctores_con_horarios.append({
            'doctor': doctor,
            'horas_disponibles': horas_disponibles
        })

    return render(request, 'seleccionar_doctor.html', {
        'doctores': doctores_con_horarios,
        'especialidad': especialidad_seleccionada,
        'fecha': fecha,
    })

@login_required
def pedir_hora(request):
    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=request.user)

    # Verificar si el usuario ya tiene una cita confirmada
    cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True).first()

    # Si ya tiene una cita, redirigir a la página de confirmación de la cita existente
    if cita_existente:
        return redirect(f"{reverse('confirmacion_cita')}?cita_id={cita_existente.id}")

    # Código para manejar el agendamiento de una nueva cita (si no existe cita)
    especialidad_seleccionada = request.GET.get('especialidad') or request.POST.get('especialidad')
    sedes = []
    error_message = None

    # Cargar las sedes si se selecciona una especialidad
    if especialidad_seleccionada:
        sedes = SedeClinica.objects.filter(
            doctorclinica__doctor__especialidad_doctor=especialidad_seleccionada
        ).distinct()

    # Validar ambos campos en el formulario POST (cuando el usuario hace clic en "Buscar Doctores")
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad')
        sede_id = request.POST.get('sede')

        # Solo redirigir si ambos campos tienen valores
        if especialidad and sede_id:
            # Redirigir a la página de selección de doctores con los parámetros en la URL
            return redirect(f"{reverse('seleccionar_doctor')}?especialidad={especialidad}&sede={sede_id}")
        
        # Mostrar mensaje de error si falta algún campo
        error_message = "Por favor, seleccione tanto la especialidad como la sede antes de continuar."

    especialidades = Doctor.objects.values_list('especialidad_doctor', flat=True).distinct()

    return render(request, 'pedir_hora.html', {
        'especialidades': especialidades,
        'sedes': sedes,
        'especialidad_seleccionada': especialidad_seleccionada,
        'error_message': error_message,
    })
    
def sedes_por_especialidad(request, especialidad):
    # Filtrar las sedes que tienen doctores con la especialidad seleccionada
    sedes = SedeClinica.objects.filter(
        doctorclinica__doctor__especialidad_doctor=especialidad
    ).distinct()

    sedes_data = [
        {'id': sede.id, 'nombre': sede.nombre_clinica, 'comuna': sede.comuna_sede}
        for sede in sedes
    ]
    
    return JsonResponse({'sedes': sedes_data})

def login_view(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        rut = request.POST.get('rut', '').strip()
        password = request.POST.get('contrasena', '')

        try:
            # Busca el usuario por RUT
            usuario = Usuario.objects.get(rut=rut)

            # Verifica la contraseña
            if usuario.check_password(password):
                # Determina el rol automáticamente
                if Paciente.objects.filter(usuario=usuario).exists():
                    rol = 'paciente'
                    login(request, usuario)
                    return redirect('inicio')
                elif Doctor.objects.filter(usuario=usuario).exists():
                    rol = 'doctor'
                    login(request, usuario)
                    return redirect('doctor_dashboard')
                else:
                    messages.error(request, 'No tienes un rol asignado en el sistema.')
                    return redirect('login')
            else:
                # Si la contraseña es incorrecta
                messages.error(request, 'Contraseña incorrecta.')
                return redirect('login')

        except Usuario.DoesNotExist:
            # Si el RUT no existe en la base de datos
            messages.error(request, 'RUT no se encuentra registrado.')
            return redirect('login')

    # Renderiza el formulario de login
    return render(request, 'consultorioCys/login.html')

@login_required
def perfil_view(request):
    usuario = request.user  # Obtiene el usuario autenticado
    # Si tienes información del doctor o paciente relacionada, puedes obtenerla así:
    try:
        doctor = Doctor.objects.get(usuario=usuario)
        return render(request, 'consultorioCys/perfil.html', {'usuario': usuario, 'doctor': doctor})
    except Doctor.DoesNotExist:
        # Si no es doctor, verifica si es paciente
        try:
            paciente = Paciente.objects.get(usuario=usuario)
            return render(request, 'consultorioCys/perfil.html', {'usuario': usuario, 'paciente': paciente})
        except Paciente.DoesNotExist:
            # Si no es doctor ni paciente
            return render(request, 'consultorioCys/perfil.html', {'usuario': usuario})

def logout_view(request):
    logout(request)
    return redirect('inicio')

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    if request.user.is_authenticated and isinstance(request.user, Doctor):
        return render(request, 'consultorioCys/doctor_dashboard.html', {'doctor': request.user})
    return redirect('login')

def is_paciente(user):
    return user.groups.filter(name='Paciente').exists()

@login_required
@user_passes_test(is_paciente)
def paciente_dashboard(request):
    if request.user.is_authenticated and isinstance(request.user, Paciente):
        return render(request, 'consultorioCys/paciente_dashboard.html', {'paciente': request.user})
    return redirect('login')

@login_required
def doctor_dashboard(request):
    if hasattr(request.user, 'paciente'):
        messages.error(request, 'No tienes permisos para acceder a esta sección como paciente.')
        return redirect('inicio')
    
    # Si el usuario es doctor, muestra el dashboard
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
def paciente_dashboard(request):
    print("Entrando al dashboard del paciente")
    return render(request, 'consultorioCys/paciente_dashboard.html')

def is_usuario(user):
    return user.groups.filter(name='Usuario').exists()

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

@login_required
@user_passes_test(is_doctor)
def add_doctor_view(request):
    if request.method == 'POST':
        form = AddDoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doctor_dashboard')  # Redirigir a algún lugar después de agregar el doctor
    else:
        form = AddDoctorForm()
    return render(request, 'consultorioCys/add_doctor.html', {'form': form})

def informe_doctores(request):
    # Obtener todos los doctores desde la base de datos
    doctores = Doctor.objects.all()

    # Pasar los datos de los doctores a la plantilla 'informe_doctores.html'
    return render(request, 'informe_doctores.html', {'doctores': doctores})

def paciente_info(request, rut_paciente):
    # Buscar el paciente usando `rut_paciente`
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    # Obtener los informes relacionados usando `informe_set`
    informes = paciente.informe_set.all().order_by('-fecha_informe')

    return render(request, 'consultorioCys/paciente_info.html', {
        'paciente': paciente,
        'informes': informes,
    })

def buscar_paciente(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')  # RUT del usuario
        clave = request.POST.get('clave')  # Clave del usuario

        try:
            # Buscar al usuario por su RUT
            usuario = Usuario.objects.get(rut=rut)

            # Verificar si la clave proporcionada es correcta
            if usuario.check_password(clave):
                try:
                    # Obtener el paciente relacionado
                    paciente = usuario.paciente

                    # Obtener los informes del paciente
                    informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')

                    # Renderizar la vista de búsqueda de paciente con los informes
                    return render(request, 'consultorioCys/buscar_paciente.html', {
                        'paciente': paciente,
                        'informes': informes
                    })

                except Paciente.DoesNotExist:
                    messages.error(request, "Este RUT no corresponde a un paciente. Inténtelo de nuevo.")
            else:
                messages.error(request, "Clave incorrecta. Inténtelo de nuevo.")
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado. Verifique el RUT e intente nuevamente.")

    # Si hay errores, volver al dashboard
    return render(request, 'consultorioCys/doctor_dashboard.html')

# Listado de pacientes
def listar_pacientes(request):
    pacientes = Paciente.objects.prefetch_related('informe_set')
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes_list.html', {'pacientes': pacientes})

# Crear un nuevo paciente
def crear_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST, request.FILES)
        if form.is_valid():
            paciente = form.save(commit=False)  # No guardes todavía el paciente
            paciente.usuario = request.user  # Asigna el usuario logueado
            paciente.save()  # Ahora guarda el paciente
            return redirect('listar_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'paciente_form.html', {'form': form})

# Editar un paciente existente
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        form = PacienteForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('listar_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'paciente_form.html', {'form': form})

# Eliminar un paciente
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        paciente.delete()
        return redirect('listar_pacientes')
    return render(request, 'confirmar_eliminar.html', {'paciente': paciente})

def informe_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    informes = Informe.objects.filter(paciente=paciente)  # Trae todos los informes del paciente
    edit_informe_id = request.POST.get('edit_informe_id')  # Identificador del informe que se va a editar

    if request.method == 'POST' and edit_informe_id:  # Si se está enviando el formulario de edición
        informe = get_object_or_404(Informe, id=edit_informe_id)
        form = InformeForm(request.POST, request.FILES, instance=informe)
        if form.is_valid():
            form.save()
            return redirect('informe_paciente', pk=paciente.pk)  # Refresca la página
    else:
        form = InformeForm()  # Formulario vacío si no estamos editando
    
    return render(request, 'informe_paciente.html', {'paciente': paciente, 'informes': informes, 'form': form})

def crear_informe(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    
    if request.method == 'POST':
        form = InformeForm(request.POST, request.FILES)
        if form.is_valid():
            informe = form.save(commit=False)
            informe.paciente = paciente  # Asigna el paciente al informe
            informe.save()
            return redirect('listar_pacientes')
    else:
        form = InformeForm()

    return render(request, 'crear_informe.html', {'form': form, 'paciente': paciente})

#formulario agendar cita y calendario en doctor 
def form_cita(request):
    # Verificar que el usuario autenticado es un paciente
    try:
        paciente = Paciente.objects.get(usuario=request.user)
    except Paciente.DoesNotExist:
        messages.error(request, 'Solo los pacientes pueden solicitar citas.')
        return redirect('inicio')  # Redirige a la página de inicio si no es paciente

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            # Crear una nueva cita
            cita = form.save(commit=False)
            cita.paciente = paciente  # Asigna el paciente actual a la cita

            # Si el paciente ya tiene un doctor asignado, lo agregamos a la cita
            if Doctor.objects.filter(usuario=request.user).exists():
                cita.doctor = Doctor.objects.get(usuario=request.user)
            
            # Guardar la cita y confirmar
            cita.save()
            messages.success(request, 'Su cita ha sido solicitada con éxito.')
            return redirect('inicio')
    else:
        form = CitaForm()

    return render(request, 'consultorioCys/form_cita.html', {'form': form})


@login_required
def ver_calendario(request):
    if request.user.is_authenticated and hasattr(request.user, 'doctor'):
        # Obtiene las citas relacionadas al doctor autenticado
        doctor = request.user.doctor
        return render(request, 'consultorioCys/ver_calendario.html', {'doctor': doctor})
    else:
        # Redirige si el usuario no es un doctor autenticado
        return redirect('inicio')

@login_required
def obtener_citas_json(request):
    if request.user.is_authenticated and hasattr(request.user, 'doctor'):
        doctor = request.user.doctor
        citas = Cita.objects.filter(doctor=doctor)
        citas_json = [
            {
                "title": f"{cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente}",
                "start": f"{cita.fecha_cita}T{cita.hora}",
                "end": f"{cita.fecha_cita}T{cita.hora}",
                "extendedProps": {
                    "tratamiento": cita.tratamiento
                }
            }
            for cita in citas
        ]
        return JsonResponse(citas_json, safe=False)
    else:
        return JsonResponse([], safe=False)

#ACA TERMINA EL CALENDARIO 


def generar_pdf(request, informe_id):
    informe = get_object_or_404(Informe, id_informe=informe_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_{informe.id_informe}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, f"Título del Informe: {informe.titulo_informe}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 720, f"Fecha: {informe.fecha_informe}")
    pdf.drawString(100, 700, f"Nombre del Paciente: {informe.paciente.nombres_paciente} {informe.paciente.apellidos_paciente}")
    pdf.drawString(100, 680, f"RUT: {informe.paciente.rut_paciente}")
    pdf.drawString(100, 660, f"Doctor: {informe.doctor.nombre_doctor}")
    pdf.drawString(100, 640, f"Clínica: {informe.clinica.nombre_clinica}")
    pdf.drawString(100, 620, f"Sede: {informe.sede.nombre_sede}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(100, 580, "Descripción del Informe")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 560, informe.descripcion_informe)

    pdf.showPage()
    pdf.save()

    return response