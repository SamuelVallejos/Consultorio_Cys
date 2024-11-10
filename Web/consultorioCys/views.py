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

def inicio(request):
    message = request.GET.get('message')
    print(f"Usuario autenticado: {request.user.is_authenticated}")
    return render(request, 'consultorioCys/inicio.html', {'message': message}) 

def ia(request):
    return render(request, 'consultorioCys/ia.html')

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
        cita.save()  # Guarda la cita en la base de datos

        # Obtener la sede asociada al doctor
        sede_relacion = doctor.doctorclinica_set.first()
        sede = sede_relacion.sede if sede_relacion else None

        # Depuración: Imprimir la sede obtenida
        if sede:
            print("Sede obtenida:", sede.clinica.nombre_clinica, sede.comuna_sede, sede.region_sede)
        else:
            print("No se encontró sede para el doctor.")
        
        # Preparar contexto con la información de la cita, incluyendo la ubicación
        context = {
            'doctor': doctor,
            'fecha': fecha,
            'hora': hora_obj.strftime("%H:%M"),
            'especialidad': doctor.especialidad_doctor,
            'ubicacion': f"{sede.clinica.nombre_clinica} - {sede.comuna_sede}, {sede.region_sede}" if sede else "Ubicación no disponible"
        }

        return render(request, 'confirmacion_cita.html', context)
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
    especialidad = request.GET.get('especialidad')
    sede_id = request.GET.get('sede')
    fecha = request.GET.get('fecha')
    error_message = None

    # Verificar que todos los parámetros necesarios estén presentes
    if not especialidad or not sede_id or not fecha:
        error_message = "Faltan algunos parámetros. Por favor, vuelva al paso anterior y seleccione una especialidad, sede y fecha."
        return render(request, 'seleccionar_doctor.html', {'error_message': error_message})

    # Obtener los doctores disponibles en la sede y especialidad especificadas
    doctor_clinica_entries = DoctorClinica.objects.filter(
        doctor__especialidad_doctor=especialidad,
        sede_id=sede_id
    ).select_related('doctor', 'sede').distinct()

    # Crear una lista de doctores con sus horas disponibles para pasar al contexto
    doctores = []
    for entry in doctor_clinica_entries:
        horas_disponibles = DisponibilidadDoctor.objects.filter(
            doctor=entry.doctor,
            fecha=fecha,
            disponible=True
        ).values_list('hora', flat=True)
        doctores.append({
            'doctor': entry.doctor,
            'sede': entry.sede,
            'horas_disponibles': horas_disponibles
        })

    # Pasar todos los datos necesarios al contexto
    context = {
        'doctores': doctores,
        'especialidad': especialidad,
        'fecha': fecha,
        'sede_id': sede_id,
        'error_message': error_message
    }
    return render(request, 'seleccionar_doctor.html', context)

def horarios_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Aquí puedes definir los horarios disponibles, por ejemplo, en intervalos de 15 minutos de 7:00 a 10:00
    horarios_disponibles = [
        "07:00", "07:15", "07:30", "07:45", "08:00",
        "08:15", "08:30", "08:45", "09:00", "09:15", "09:30"
    ]
    
    return render(request, 'horarios_doctor.html', {
        'doctor': doctor,
        'horarios': horarios_disponibles,
    })

@login_required
def pedir_hora(request):
    especialidad_seleccionada = request.GET.get('especialidad') or request.POST.get('especialidad')
    fecha_seleccionada = request.GET.get('fecha') or request.POST.get('fecha')
    sedes = []
    error_message = None

    # Cargar las sedes si se selecciona una especialidad
    if especialidad_seleccionada:
        sedes = SedeClinica.objects.filter(
            doctorclinica__doctor__especialidad_doctor=especialidad_seleccionada
        ).distinct()

    # Validar los campos en el formulario POST (cuando el usuario hace clic en "Buscar Doctores")
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad')
        sede_id = request.POST.get('sede')
        fecha = request.POST.get('fecha')

        # Debug: imprimir valores en consola para verificar
        print("Especialidad:", especialidad)
        print("Sede ID:", sede_id)
        print("Fecha:", fecha)

        # Solo redirigir si todos los campos tienen valores
        if especialidad and sede_id and fecha:
            # Redirigir a la página de selección de doctores con los parámetros en la URL
            return redirect(f"{reverse('seleccionar_doctor')}?especialidad={especialidad}&sede={sede_id}&fecha={fecha}")
        
        # Mostrar mensaje de error si falta algún campo
        error_message = "Por favor, seleccione la especialidad, la sede y la fecha antes de continuar."

    # Obtener lista de especialidades
    especialidades = Doctor.objects.values_list('especialidad_doctor', flat=True).distinct()

    return render(request, 'pedir_hora.html', {
        'especialidades': especialidades,
        'sedes': sedes,
        'especialidad_seleccionada': especialidad_seleccionada,
        'fecha_seleccionada': fecha_seleccionada,
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
        rut = request.POST.get('rut', '').strip()  # Elimina espacios extra
        password = request.POST.get('contrasena', '')
        rol = request.POST.get('rol', '').lower()  # Asegura que el rol esté en minúsculas

        # Imprimir todos los datos recibidos para depuración
        print("===== Datos del Formulario de Login =====")
        print(f"RUT: {rut}")
        print(f"Contraseña: {password}")
        print(f"Rol: {rol}")
        print(f"POST Data: {request.POST}")  # Imprime todos los datos enviados

        try:
            # Busca el usuario por RUT
            usuario = Usuario.objects.get(rut=rut)

            # Verifica la contraseña
            if usuario.check_password(password):
                if rol == 'paciente':
                    # Verificar si el usuario tiene un paciente relacionado
                    if Paciente.objects.filter(usuario=usuario).exists():
                        login(request, usuario)  # Inicia sesión como paciente
                        return redirect('inicio')  # Redirige al inicio del paciente
                    else:
                        messages.error(request, 'No estás registrado como paciente.')
                        return redirect('login')

                elif rol == 'doctor':
                    # Verificar si el usuario tiene un doctor relacionado
                    if Doctor.objects.filter(usuario=usuario).exists():
                        login(request, usuario)  # Inicia sesión como doctor
                        return redirect('doctor_dashboard')  # Redirige al dashboard del doctor
                    else:
                        messages.error(request, 'No estás registrado como doctor.')
                        return redirect('login')

                else:
                    # Rol no válido o no coincide
                    messages.error(request, 'Rol inválido. Por favor, selecciona un rol válido.')
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

                    # Redirigir usando reverse() para asegurar la ruta
                    from django.urls import reverse
                    url = reverse('paciente_info', kwargs={'rut_paciente': paciente.rut_paciente})
                    return redirect(url)
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
