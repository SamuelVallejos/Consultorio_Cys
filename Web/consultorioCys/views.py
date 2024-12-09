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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import Http404
from PIL import Image
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import datetime
import random
import string
import os
from .ai_processor import analyze_informe
from django.http import JsonResponse
from django.db.models import Q
from .ai_processor import preprocess_text
from django.core.paginator import Paginator
from .models import Plan, Suscripcion, Transaccion, MetodoPago
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
from .models import MetodoPago
from .forms import PagoForm
from .forms import InformeExternoForm

@login_required
def agregar_doc_personal(request, rut_paciente):
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)
    if request.method == 'POST':
        form = InformeExternoForm(request.POST, request.FILES)
        if form.is_valid():
            # Obtener los datos del formulario
            titulo = form.cleaned_data['titulo_informe']
            rut_doctor = form.cleaned_data['rut_doctor']
            nombre_doctor = form.cleaned_data['nombre_doctor']
            documento = form.cleaned_data['documentos_extra']

            # Intenta relacionar con un doctor existente
            try:
                doctor = Doctor.objects.get(rut_doctor=rut_doctor)
            except Doctor.DoesNotExist:
                doctor = None  # Si no existe, deja el campo vacío

            # Crear el informe
            informe = Informe.objects.create(
                titulo_informe=titulo,
                paciente=paciente,
                doctor=doctor,  # Puede ser None si no existe
                documentos_extra=documento,
                notas_doctor=nombre_doctor if not doctor else "",  # Solo guarda el nombre si no hay doctor
            )
            informe.save()

            # Redirigir a la página historial_personal
            return redirect('historial_personal')
    else:
        form = InformeExternoForm()

    return render(request, 'agregar_doc_personal.html', {'form': form, 'paciente': paciente})

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

def registro_view(request):
    if request.method == 'POST':
        rut = request.POST['rut']
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        tipo_usuario = request.POST['tipo_usuario']
        plan_id = request.POST['plan']
        tarjeta_numero = request.POST['tarjeta_numero']
        tarjeta_tipo = request.POST['tarjeta_tipo']

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('registro')

        try:
            usuario = Usuario.objects.create(
                rut=rut,
                nombre=nombre,
                apellido=apellido,
                email=email,
            )
            usuario.set_password(password)
            usuario.save()

            if tipo_usuario == 'paciente':
                Paciente.objects.create(
                    usuario=usuario,
                    rut_paciente=rut,
                    nombres_paciente=nombre,
                    primer_apellido_paciente=apellido,
                    correo_paciente=email,
                    telefono_paciente=request.POST.get('telefono_paciente'),
                    direccion_paciente=request.POST.get('direccion_paciente'),
                )
            elif tipo_usuario == 'doctor':
                Doctor.objects.create(
                    usuario=usuario,
                    rut_doctor=rut,
                    nombres_doctor=nombre,
                    primer_apellido_doctor=apellido,
                    correo_doctor=email,
                    especialidad_doctor=request.POST.get('especialidad_doctor'),
                )

            # Crear suscripción
            plan = Plan.objects.get(id_plan=plan_id)
            Suscripcion.objects.create(
                paciente=Paciente.objects.get(usuario=usuario) if tipo_usuario == 'paciente' else None,
                plan=plan,
                fecha_inicio=now(),
                fecha_fin=now() + timedelta(days=30),  # Vigencia de 30 días
                renovado=False,
            )

            messages.success(request, "Registro y suscripción completados correctamente.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Error al registrar usuario: {str(e)}")
            return redirect('registro')

    planes = Plan.objects.all()
    return render(request, 'consultorioCys/registro.html', {'planes': planes})

@login_required
def cambiar_clave_usuario(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Validar la contraseña antigua
        if not user.check_password(old_password):
            messages.error(request, 'La contraseña actual no es correcta.')
            return render(request, 'consultorioCys/cambiar_clave_usuario.html')

        # Validar que las contraseñas nuevas coincidan
        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'consultorioCys/cambiar_clave_usuario.html')

        # Cambiar la contraseña
        user.password = make_password(new_password)
        user.save()
        messages.success(request, 'La contraseña ha sido cambiada exitosamente.')
        return redirect('perfil')  # Redirigir al perfil del usuario

    return render(request, 'consultorioCys/cambiar_clave_usuario.html')

User = get_user_model()

def cambiar_clave(request, uidb64, token):
    try:
        # Decodificar el UID para obtener al usuario
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Validar el token
        if not default_token_generator.check_token(user, token):
            return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'El enlace no es válido o ha expirado.'})

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                # Cambiar la contraseña
                user.password = make_password(new_password)
                user.save()
                return redirect('login')  # Redirige al login después del cambio exitoso
            else:
                return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'Las contraseñas no coinciden.'})

        return render(request, 'consultorioCys/cambiar_clave.html', {'uidb64': uidb64, 'token': token})
    except (User.DoesNotExist, ValueError, TypeError):
        return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'Ha ocurrido un error. Intenta nuevamente.'})

def restablecer_clave(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Enlace para el correo
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            link = f"{protocol}://{domain}/cambiar_clave/{uidb64}/{token}"

            # Renderizar plantilla del correo
            email_subject = 'Restablecimiento de contraseña'
            email_body = render_to_string('consultorioCys/mensaje_cambio_clave.txt', {
                'protocol': protocol,
                'domain': domain,
                'uid': uidb64,
                'token': token,
                'site_name': 'Consultorio Cys',
            })

            # Enviar el correo
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, f"Se ha enviado un mensaje a tu correo {user.email}")
            return render(request, 'consultorioCys/restablecer_clave.html', {'mensaje': 'Correo enviado.'})
        except User.DoesNotExist:
            messages.error(request, "El correo electrónico ingresado no está registrado.")
            return render(request, 'consultorioCys/restablecer_clave.html', {'error': 'Correo no encontrado.'})

    return render(request, 'consultorioCys/restablecer_clave.html')

def acercade(request):
    return render(request, 'consultorioCys/acercade.html')

@login_required
def historial_personal(request):
    usuario = request.user
    paciente = get_object_or_404(Paciente, usuario=usuario)
    informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')
    paginator = Paginator(informes, 10)  # Máximo 10 informes por página
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number) 
    informe_reciente = informes.first() if informes.exists() else None
    citas = Cita.objects.filter(
        paciente=paciente,
        fecha_cita__gte=timezone.now().date()
    ).order_by('fecha_cita', 'hora_cita')
    doctor = informe_reciente.doctor if informe_reciente else None
    clinica = informe_reciente.clinica if informe_reciente else None
    sede = informe_reciente.sede if informe_reciente else None

    context = {
        'paciente': paciente,
        'rut_paciente': paciente.rut_paciente,  # Utiliza el atributo correcto
        'informes': page_obj,  # Usar la página actual de informes
        'informe_reciente': informe_reciente,  # Informe más reciente
        'doctor': doctor,
        'clinica': clinica,
        'sede': sede,
        'citas': citas,
    }
    return render(request, 'consultorioCys/historial_personal.html', context)

@login_required
def detalle_informe(request, pk):
    informe = get_object_or_404(Informe, pk=pk)

    return render(request, 'consultorioCys/detalle_informe.html', {'informe': informe})

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
        paciente = request.user.paciente  
        doctor = get_object_or_404(Doctor, id=doctor_id)
        nueva_cita = Cita.objects.create(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha_cita,
            hora_cita=hora_cita,
            motivo_consulta=request.POST.get("motivo_consulta", ""),
            confirmado=True
        )
        return redirect("resumen_cita", cita_id=nueva_cita.id)
    else:
        return redirect("pedir_hora")
    
@login_required
def confirmacion_cita(request):
    paciente = get_object_or_404(Paciente, usuario=request.user)

    if request.method == 'POST':
        # Manejo de cancelación de cita
        if 'cancelar_cita' in request.POST:
            cita_id = request.POST.get('cita_id')
            cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)

            # Buscar la disponibilidad asociada y marcarla como disponible
            disponibilidad = DisponibilidadDoctor.objects.filter(
                doctor=cita.doctor,
                fecha=cita.fecha_cita,
                hora=cita.hora_cita
            ).first()

            if disponibilidad:
                disponibilidad.disponible = True
                disponibilidad.save()

            # Marcar la cita como finalizada
            cita.finalizada = True
            cita.save()

            return redirect('confirmacion_cita')  # Redirigir para actualizar la lista de citas

        # Manejo de activación de cita
        doctor_id = request.POST.get('doctor_id')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if not doctor_id or not fecha or not hora:
            return render(request, 'consultorioCys/confirmacion_cita.html', {
                'error': 'Faltan datos necesarios para agendar la cita.'
            })

        doctor = get_object_or_404(Doctor, rut_doctor=doctor_id)

        try:
            hora_obj = datetime.datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return render(request, 'consultorioCys/confirmacion_cita.html', {
                'error': f'El formato de la hora recibido ({hora}) no es válido. Debe estar en el formato HH:MM.'
            })

        # Verificar que la hora aún esté disponible
        disponibilidad = DisponibilidadDoctor.objects.filter(
            doctor=doctor,
            fecha=fecha,
            hora=hora_obj,
            disponible=True
        ).first()

        if not disponibilidad:
            return render(request, 'consultorioCys/confirmacion_cita.html', {
                'error': 'La hora seleccionada ya no está disponible. Por favor, seleccione otra.'
            })

        # Crear la cita
        cita = Cita(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha,
            hora_cita=hora_obj,
            confirmado=True
        )
        cita.save()

        # Marcar la hora como no disponible
        disponibilidad.disponible = False
        disponibilidad.save()

        doctor_clinica = DoctorClinica.objects.filter(doctor=doctor).first()
        sede = doctor_clinica.sede if doctor_clinica else None

        context = {
            'doctor': doctor,
            'fecha': fecha,
            'hora': hora_obj.strftime("%H:%M"),
            'especialidad': doctor.especialidad_doctor,
            'ubicacion': f"{sede.clinica.nombre_clinica} - {sede.comuna_sede}, {sede.region_sede}" if sede else "Ubicación no disponible",
            'citas': Cita.objects.filter(paciente=paciente, finalizada=False).distinct().order_by('fecha_cita', 'hora_cita')
        }

        return render(request, 'consultorioCys/confirmacion_cita.html', context)

    elif request.method == 'GET':
        # Mostrar citas activas
        citas = Cita.objects.filter(paciente=paciente, finalizada=False).distinct().order_by('fecha_cita', 'hora_cita')
        context = {'citas': citas} if citas.exists() else {'error': 'No tienes citas activas en este momento.'}

        return render(request, 'consultorioCys/confirmacion_cita.html', context)

    # Método no permitido
    return render(request, 'consultorioCys/confirmacion_cita.html', {
        'error': 'Método de solicitud no válido.'
    })
    
@login_required
def finalizar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if not hasattr(request.user, 'doctor') or request.user.doctor != cita.doctor:
        messages.error(request, 'No tienes permiso para finalizar esta cita.')
        return redirect('ver_calendario')

    cita.finalizada = True
    cita.save()

    disponibilidad = DisponibilidadDoctor.objects.filter(
        doctor=cita.doctor,
        fecha=cita.fecha_cita,
        hora=cita.hora_cita
    )
    if disponibilidad.exists():
        disponibilidad.update(disponible=True)

    # Enviar un mensaje de confirmación y redirigir al calendario del doctor
    messages.success(request, f'La cita con el paciente {cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente} ha sido finalizada con éxito.')
    return redirect('ver_calendario')  # Cambia esto según dónde desees redirigir al doctor
    
@login_required
def seleccionar_doctor(request):
    especialidad_seleccionada = request.GET.get('especialidad')
    fecha = request.GET.get('fecha')  # Fecha seleccionada desde el formulario

    doctores = Doctor.objects.filter(especialidad_doctor=especialidad_seleccionada)
    doctores_con_horarios = []

    hora_actual = datetime.datetime.now().time()  # Hora actual
    fecha_actual = str(datetime.date.today())  # Fecha actual en formato "YYYY-MM-DD"

    for doctor in doctores:
        # Filtrar horas disponibles basadas en la fecha
        if fecha == fecha_actual:
            # Mostrar solo horas mayores a la hora actual si la fecha es hoy
            horas_disponibles = DisponibilidadDoctor.objects.filter(
                doctor=doctor,
                fecha=fecha,
                hora__gte=hora_actual,
                disponible=True
            ).values_list('hora', flat=True)
        else:
            # Mostrar todas las horas disponibles para fechas futuras
            horas_disponibles = DisponibilidadDoctor.objects.filter(
                doctor=doctor,
                fecha=fecha,
                disponible=True
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
    paciente = get_object_or_404(Paciente, usuario=request.user)

    citas_activas = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).count()

    cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).first()

    if citas_activas >= 3:
        return render(request, 'confirmacion_cita.html', {
            'mensaje_error': 'No puedes agendar más de 3 citas activas. Cancela alguna para agendar una nueva.',
            'citas_activas': citas_activas,
            'cita_existente': cita_existente,
        })

    especialidad_seleccionada = request.GET.get('especialidad') or request.POST.get('especialidad')
    sedes = []
    error_message = None

    if especialidad_seleccionada:
        sedes = SedeClinica.objects.filter(
            doctorclinica__doctor__especialidad_doctor=especialidad_seleccionada
        ).distinct()

    if request.method == 'POST':
        especialidad = request.POST.get('especialidad')
        sede_id = request.POST.get('sede')
        fecha = request.POST.get('fecha')

        if especialidad and sede_id and fecha:
            return redirect(
                f"{reverse('seleccionar_doctor')}?especialidad={especialidad}&sede={sede_id}&fecha={fecha}"
            )

        error_message = "Por favor, seleccione la especialidad, la sede y la fecha antes de continuar."

    especialidades = Doctor.objects.values_list('especialidad_doctor', flat=True).distinct()

    return render(request, 'pedir_hora.html', {
        'especialidades': especialidades,
        'sedes': sedes,
        'especialidad_seleccionada': especialidad_seleccionada,
        'error_message': error_message,
        'citas_activas': citas_activas,
        'cita_existente': cita_existente,
    })

def sedes_por_especialidad(request, especialidad):
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
        rut = request.POST.get('rut', '').strip()
        password = request.POST.get('contrasena', '')

        try:
            usuario = Usuario.objects.get(rut=rut)

            if usuario.check_password(password):
                # Iniciar sesión
                login(request, usuario)

                # Verificar si el usuario es un Paciente
                if Paciente.objects.filter(usuario=usuario).exists():
                    paciente = Paciente.objects.get(usuario=usuario)
                    suscripcion_activa = Suscripcion.objects.filter(
                        paciente=paciente, fecha_fin__gte=now()
                    ).exists()

                    if not suscripcion_activa:
                        # Redirigir directamente a la página de renovación de suscripción vencida
                        return redirect('renovar_suscripcion_vencida', rut=paciente.rut_paciente)

                    # Redirigir al inicio si la suscripción está activa
                    return redirect('inicio')

                # Verificar si el usuario es un Doctor
                elif Doctor.objects.filter(usuario=usuario).exists():
                    return redirect('doctor_dashboard')

                # Usuario sin rol asignado
                else:
                    messages.error(
                        request, 'No tienes un rol asignado en el sistema. Por favor, contacta al administrador.'
                    )
                    return redirect('login')

            # Contraseña incorrecta
            else:
                messages.error(request, 'Contraseña incorrecta.')
                return redirect('login')

        except Usuario.DoesNotExist:
            # Usuario no registrado
            messages.error(request, 'El RUT ingresado no se encuentra registrado.')
            return redirect('login')

    return render(request, 'consultorioCys/login.html')

@login_required
def perfil_view(request):
    usuario = request.user

    # Variables iniciales
    plan_actual = None
    fecha_fin = None
    suscripcion = None
    datos_usuario = {}

    # Si el usuario es un paciente
    if hasattr(usuario, 'paciente'):
        paciente = usuario.paciente
        suscripcion = Suscripcion.objects.filter(paciente=paciente).order_by('-fecha_inicio').first()
        if suscripcion:
            plan_actual = suscripcion.plan
            fecha_fin = suscripcion.fecha_fin
        # Datos específicos del paciente
        datos_usuario = {
            'nombre': paciente.nombres_paciente,
            'apellido': f"{paciente.primer_apellido_paciente} {paciente.segundo_apellido_paciente or ''}".strip(),
            'email': paciente.correo_paciente,
            'telefono': paciente.telefono_paciente,
            'fecha_nacimiento': paciente.fecha_nacimiento_paciente,
            'genero': paciente.get_genero_paciente_display(),
            'direccion': paciente.direccion_paciente,
        }

        # Actualizar datos del paciente
        if request.method == 'POST':
            email = request.POST.get('email')
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')

            if email:
                paciente.correo_paciente = email
            if telefono:
                paciente.telefono_paciente = telefono
            if direccion:
                paciente.direccion_paciente = direccion
            paciente.save()
            messages.success(request, 'Tus datos se han actualizado correctamente.')
            return redirect('perfil')

    # Si el usuario es un doctor
    elif hasattr(usuario, 'doctor'):
        doctor = usuario.doctor
        datos_usuario = {
            'nombre': doctor.nombres_doctor,
            'apellido': f"{doctor.primer_apellido_doctor} {doctor.segundo_apellido_doctor or ''}".strip(),
            'email': doctor.correo_doctor,
            'telefono': doctor.telefono_doctor,
            'fecha_nacimiento': doctor.fecha_nacimiento_doctor,
            'especialidad': doctor.especialidad_doctor,
        }

        # Actualizar datos del doctor
        if request.method == 'POST':
            email = request.POST.get('email')
            telefono = request.POST.get('telefono')
            especialidad = request.POST.get('especialidad')

            if email:
                doctor.correo_doctor = email
            if telefono:
                doctor.telefono_doctor = telefono
            if especialidad:
                doctor.especialidad_doctor = especialidad
            doctor.save()
            messages.success(request, 'Tus datos se han actualizado correctamente.')
            return redirect('perfil')

    return render(request, 'consultorioCys/perfil.html', {
        'usuario': usuario,
        'datos_usuario': datos_usuario,
        'plan_actual': plan_actual,
        'fecha_fin': fecha_fin,
        'suscripcion': suscripcion,
    })

@login_required
def mi_suscripcion(request):
    usuario = request.user

    # Inicializar valores
    suscripcion = None
    dias_restantes = None
    plan_actual = None

    # Verificar si el usuario está asociado a un paciente
    if hasattr(usuario, 'paciente'):
        paciente = usuario.paciente
        suscripcion = Suscripcion.objects.filter(paciente=paciente).last()

        if suscripcion:
            plan_actual = suscripcion.plan
            dias_restantes = (suscripcion.fecha_fin - now()).days if suscripcion.fecha_fin else None

    return render(request, 'consultorioCys/mi_suscripcion.html', {
        'suscripcion': suscripcion,
        'plan_actual': plan_actual,
        'dias_restantes': dias_restantes,
    })

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

@login_required
def buscar_paciente(request, rut_paciente=None):
    if rut_paciente:
        try:
            paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)
            informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')
            cita_activa = Cita.objects.filter(
                paciente=paciente,
                doctor=request.user.doctor,
                finalizada=False
            ).first()

            if request.method == 'POST':
                if 'finalizar_cita' in request.POST:
                    cita_id = request.POST.get('cita_id')
                    cita = get_object_or_404(Cita, id=cita_id, paciente=paciente, doctor=request.user.doctor)
                    cita.finalizada = True
                    cita.save()
                    messages.success(request, "La cita ha sido finalizada correctamente.")
                    return redirect('buscar_paciente', rut_paciente=rut_paciente)

                if 'selected_diagnosis' in request.POST:
                    informe_id = request.POST.get('informe_id')
                    selected_diagnosis = request.POST.get('selected_diagnosis')

                    if hasattr(request.user, 'doctor'):
                        doctor_name = f"{request.user.doctor.nombres_doctor} {request.user.doctor.primer_apellido_doctor}"
                    else:
                        doctor_name = "Doctor desconocido"

                    try:
                        informe = get_object_or_404(Informe, id_informe=informe_id)

                        informe.notas_doctor = f"Diagnóstico seleccionado: {selected_diagnosis} (por: {doctor_name})"
                        informe.save()

                        messages.success(request, "Diagnóstico aplicado correctamente.")
                        return redirect('buscar_paciente', rut_paciente=rut_paciente)
                    except Informe.DoesNotExist:
                        messages.error(request, "El informe seleccionado no existe.")

            for informe in informes:
                analysis_result = analyze_informe(informe.descripcion_informe)

                most_probable = analysis_result["most_probable"]
                confidence = analysis_result["confidence"]
                alternatives = analysis_result["alternatives"]

                ia_diagnoses = [
                    {"text": f"{alt['diagnosis']} (sugerido por IA)", "confidence": alt["confidence"]}
                    for alt in alternatives
                ]

                doctor_diagnosis = [
                    {"text": f"{informe.notas_doctor or 'Sin diagnóstico previo'} (actual del doctor)", "confidence": None}
                ]

                informe.diagnosis_suggestions = doctor_diagnosis + ia_diagnoses

            return render(request, 'consultorioCys/buscar_paciente.html', {
                'paciente': paciente,
                'informes': informes,
                'cita_activa': cita_activa, 
            })
        except Paciente.DoesNotExist:
            messages.error(request, "Este RUT no corresponde a un paciente.")
            return redirect('doctor_dashboard')

    return redirect('doctor_dashboard')

@login_required
def listar_pacientes(request):
    pacientes = Paciente.objects.prefetch_related('informe_set')
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes_list.html', {'pacientes': pacientes})

Usuario = get_user_model()
@login_required
def crear_paciente(request):
    if request.method == 'POST':
        # Recopilar datos del formulario
        rut = request.POST.get('rut')
        nombres = request.POST.get('nombres')
        primer_apellido = request.POST.get('primer_apellido')
        segundo_apellido = request.POST.get('segundo_apellido')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        direccion = request.POST.get('direccion')
        genero = request.POST.get('genero')
        archivo = request.FILES.get('archivo')

        # Generar una contraseña aleatoria
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        try:
            # Crear el usuario
            usuario = Usuario.objects.create_user(
                rut=rut,
                email=correo,
                password=password,
                nombre=nombres,
                apellido=primer_apellido,
            )

            # Crear el paciente asociado
            paciente = Paciente.objects.create(
                usuario=usuario,
                rut_paciente=rut,
                nombres_paciente=nombres,
                primer_apellido_paciente=primer_apellido,
                segundo_apellido_paciente=segundo_apellido,
                correo_paciente=correo,
                telefono_paciente=telefono,
                fecha_nacimiento_paciente=fecha_nacimiento,
                direccion_paciente=direccion,
                genero_paciente=genero,
                archivo=archivo,
            )

            # Opcional: Enviar mensaje al usuario (correo con la contraseña generada)
            # Aquí puedes integrar una función para enviar la contraseña al correo.

            messages.success(request, f"El paciente {nombres} ha sido registrado con éxito. Contraseña: {password}")
            return redirect('listar_pacientes')  # Redirigir a la vista que corresponda
        except Exception as e:
            messages.error(request, f"Error al registrar el paciente: {e}")
            return redirect('crear_paciente')

    return render(request, 'consultorioCys/crear_paciente.html')

@login_required
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

@login_required
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        paciente.delete()
        return redirect('listar_pacientes')
    return render(request, 'confirmar_eliminar.html', {'paciente': paciente})

@login_required
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

@login_required
def crear_informe(request, rut_paciente):
    doctor = get_object_or_404(Doctor, usuario=request.user)
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    # Obtener la clínica y sede asociada al doctor
    doctor_clinica = DoctorClinica.objects.filter(doctor=doctor).first()
    clinica = doctor_clinica.sede.clinica if doctor_clinica else None
    sede = doctor_clinica.sede if doctor_clinica else None

    if request.method == 'POST':
        form = InformeForm(request.POST, request.FILES)
        if form.is_valid():
            informe = form.save(commit=False)  # No guardar aún
            informe.doctor = doctor  # Asignar el doctor automáticamente
            informe.paciente = paciente  # Asignar el paciente
            informe.clinica = clinica  # Asignar la clínica
            informe.sede = sede  # Asignar la sede
            informe.save()  # Guardar el informe
            messages.success(request, "El informe se creó exitosamente.")
            # Redirigir correctamente con el argumento necesario
            return redirect('buscar_paciente', rut_paciente=paciente.rut_paciente)
        else:
            print("Errores del formulario:", form.errors)
            messages.error(request, "Error al procesar el formulario. Verifica los datos ingresados.")
    else:
        form = InformeForm()

    return render(request, 'consultorioCys/crear_informe.html', {
        'form': form,
        'paciente': paciente
    })

@login_required
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
    # Obtener el médico asociado al usuario autenticado
    doctor = Doctor.objects.get(usuario=request.user)

    # Obtener las citas confirmadas de la base de datos
    citas = Cita.objects.filter(doctor=doctor, confirmado=True)

    # Formatear los datos en el backend para pasarlos al template
    eventos = [
        {
            'title': f"{cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente}",
            'start': f"{cita.fecha_cita}T{cita.hora_cita}",
            'end': f"{cita.fecha_cita}T{(datetime.datetime.combine(cita.fecha_cita, cita.hora_cita) + datetime.timedelta(minutes=30)).time()}",
            'className': 'evento-finalizado' if cita.finalizada else 'evento-pendiente',  # Clase CSS según el estado
            'extendedProps': {
                'tratamiento': cita.motivo_consulta or "Consulta General",
                'rut_paciente': cita.paciente.rut_paciente,  # Pasar el RUT del paciente
            },
        }
        for cita in citas
    ]
    # Pasar los eventos como contexto al template
    return render(request, 'consultorioCys/ver_calendario.html', {'eventos': eventos})

@login_required
def iniciar_sesion_paciente(request, rut_paciente):
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    if request.method == 'POST':
        clave_ingresada = request.POST.get('clave')
        if paciente.usuario.check_password(clave_ingresada):
            return redirect('buscar_paciente', rut_paciente=rut_paciente)
        else:
            messages.error(request, "Contraseña incorrecta. Intente de nuevo.")

    return render(request, 'consultorioCys/iniciar_sesion_paciente.html', {'paciente': paciente})

@login_required
def obtener_citas_json(request):
    # Obtener el doctor asociado al usuario autenticado
    doctor = Doctor.objects.get(usuario=request.user)

    # Filtrar citas confirmadas
    citas = Cita.objects.filter(doctor=doctor, confirmado=True)

    # Formatear eventos
    eventos = []
    for cita in citas:
        eventos.append({
            'title': f"{cita.hora_cita.strftime('%H:%M')} {cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente}",
            'start': f"{cita.fecha_cita}T{cita.hora_cita}",
            'color': '#007bff',  # Azul personalizado
        })

    return JsonResponse(eventos, safe=False)

@login_required
def generar_pdf(request, informe_id):
    # Obtener el informe desde la base de datos
    informe = get_object_or_404(Informe, id_informe=informe_id)

    # Configuración del archivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_{informe.id_informe}.pdf"'

    # Crear el PDF
    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Ruta del logo
    logo_path = os.path.join(settings.MEDIA_ROOT, 'img/logo-png.png')

    # Encabezado con logo
    if os.path.exists(logo_path):
        pdf.drawImage(logo_path, 50, height - 100, width=100, height=100)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, "INFORME MÉDICO")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(200, height - 70, f"Emitido por: {informe.doctor.nombres_doctor} {informe.doctor.primer_apellido_doctor}")
    pdf.drawString(200, height - 85, f"Especialidad: {informe.doctor.especialidad_doctor}")
    pdf.drawString(200, height - 100, f"Teléfono: {informe.doctor.telefono_doctor}")

    # Línea divisoria
    pdf.line(50, height - 120, 550, height - 120)

    # Información del paciente
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 140, "Datos del Paciente")
    patient_data = [
        ["Nombre:", f"{informe.paciente.nombres_paciente} {informe.paciente.primer_apellido_paciente}"],
        ["RUT:", informe.paciente.rut_paciente],
        ["Género:", informe.paciente.get_genero_paciente_display()],
        ["Fecha de Nacimiento:", informe.paciente.fecha_nacimiento_paciente.strftime('%d-%m-%Y')],
        ["Teléfono:", informe.paciente.telefono_paciente],
        ["Dirección:", informe.paciente.direccion_paciente]
    ]

    table = Table(patient_data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 300)

    # Información del informe
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 320, "Datos del Informe")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 340, f"Título: {informe.titulo_informe}")
    pdf.drawString(50, height - 360, f"Fecha: {informe.fecha_informe.strftime('%d-%m-%Y')}")
    pdf.drawString(50, height - 380, "Descripción:")
    pdf.setFont("Helvetica", 10)

    y = height - 400
    for line in informe.descripcion_informe.split('\n'):
        pdf.drawString(70, y, line)
        y -= 15
        if y < 100:
            pdf.showPage()
            y = height - 50

    # Diagnóstico Seleccionado
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y - 20, "Diagnóstico Seleccionado:")
    pdf.setFont("Helvetica", 10)
    y -= 40
    diagnosis_text = informe.notas_doctor or "Sin diagnóstico disponible."
    for line in diagnosis_text.split('\n'):
        pdf.drawString(70, y, line)
        y -= 15
        if y < 100:
            pdf.showPage()
            y = height - 50

    # Pie de página con información de la clínica
    pdf.setFont("Helvetica", 10)
    footer_y_position = 50
    if informe.clinica and informe.sede:
        pdf.drawString(50, footer_y_position, f"Consultorio Cys - {informe.clinica.nombre_clinica}")
        pdf.drawString(50, footer_y_position - 10, f"Dirección: {informe.sede.direccion_sede}, {informe.sede.comuna_sede}, {informe.sede.region_sede} - Teléfono: {informe.sede.telefono_sede}")
    else:
        pdf.drawString(50, footer_y_position, "Consultorio Cys")
        pdf.drawString(50, footer_y_position - 10, "Dirección: No disponible")

    # Guardar el PDF
    pdf.save()
    return response

@login_required
def descargar_como_pdf(request, path):
    # Ruta del archivo original
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("El archivo no existe.")

    # Configurar la respuesta como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(os.path.basename(path))[0]}.pdf"'

    # Crear el objeto canvas
    pdf = canvas.Canvas(response, pagesize=letter)

    # Si es una imagen, incluirla en el PDF
    try:
        img = Image.open(file_path)
        img_width, img_height = img.size

        # Escalar la imagen para ajustarse al tamaño del PDF
        page_width, page_height = letter
        scale = min(page_width / img_width, page_height / img_height)
        img_width = int(img_width * scale)
        img_height = int(img_height * scale)

        # Dibujar la imagen en el PDF
        pdf.drawImage(file_path, 0, page_height - img_height, img_width, img_height)

    except Exception:
        # Si no es una imagen, simplemente incluir el nombre del archivo en el PDF
        pdf.drawString(100, 750, "El archivo no es compatible para incrustar directamente en PDF.")
        pdf.drawString(100, 730, f"Archivo original: {os.path.basename(path)}")

    # Finalizar y cerrar el PDF
    pdf.showPage()
    pdf.save()

    return response
@login_required
def seleccionar_plan(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')  # Obtener el id_plan enviado desde el formulario
        plan = Plan.objects.get(id_plan=plan_id)  # Aquí cambiamos a id_plan
        try:
            paciente = Paciente.objects.get(usuario=request.user)  # Buscar el paciente asociado
        except Paciente.DoesNotExist:
            # Si no hay un paciente asociado, redirigir o manejar el error
            messages.error(request, "No estás registrado como paciente. Por favor, completa tu perfil primero.")
            return redirect('registro')  # Redirigir al registro

        # Crear la suscripción
        fecha_fin = now() + timedelta(days=30)  # Duración de 1 mes
        Suscripcion.objects.create(
            paciente=paciente,
            plan=plan,
            fecha_fin=fecha_fin,
        )
        return redirect('registro')  # Redirigir a la página de registro
    planes = Plan.objects.all()
    return render(request, 'consultorioCys/seleccionar_plan.html', {'planes': planes})
@login_required
def renovar_suscripcion(request):
    try:
        paciente = Paciente.objects.get(usuario=request.user)  # Obtener el paciente asociado al usuario
    except Paciente.DoesNotExist:
        messages.error(request, "No tienes un perfil de paciente asociado. Por favor, completa tu registro.")
        return redirect('registro')  # Redirigir al registro si no hay paciente asociado

    # Obtener la última suscripción del paciente
    suscripcion = Suscripcion.objects.filter(paciente=paciente).last()

    if suscripcion:
        if suscripcion.fecha_fin < now():  # Verificar si la suscripción está vencida
            suscripcion.fecha_fin = now() + timedelta(days=30)  # Renueva por 30 días
            suscripcion.renovado = True
            suscripcion.save()
            messages.success(request, "Tu plan ha sido renovado exitosamente. Fecha de expiración actualizada.")
        else:
            messages.info(request, "Tu suscripción aún está activa. No necesitas renovarla.")
    else:
        messages.error(request, "No tienes una suscripción activa para renovar. Por favor, selecciona un plan.")

    return redirect('perfil')

class ValidarSuscripcionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            suscripcion = Suscripcion.objects.filter(usuario=request.user).last()
            if not suscripcion or suscripcion.fecha_fin < now():
                return redirect('renovar_suscripcion')  # Redirigir si la suscripción no es válida
        return self.get_response(request)

#Pagos

def procesar_pago(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirigir a login si no está autenticado

    # Validar si el usuario tiene un método de pago registrado
    metodo_pago = MetodoPago.objects.filter(usuario=request.user).last()
    if not metodo_pago:
        messages.error(request, "No tienes un método de pago registrado. Por favor, agrega uno antes de continuar.")
        return redirect('perfil')

    # Obtener la suscripción actual del usuario
    suscripcion = Suscripcion.objects.filter(usuario=request.user).last()

    if not suscripcion:
        messages.error(request, "No tienes una suscripción activa para renovar.")
        return redirect('seleccionar_plan')

    plan = suscripcion.plan
    monto = plan.precio  # Precio del plan
    nueva_fecha_fin = max(suscripcion.fecha_fin, now()) + timedelta(days=30)  # Extender 30 días

    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            # Registrar transacción
            transaccion = Transaccion.objects.create(
                usuario=request.user,
                plan=plan,
                monto=monto,
                estado="Exitoso"
            )

            # Actualizar suscripción
            suscripcion.fecha_fin = nueva_fecha_fin
            suscripcion.renovado = True
            suscripcion.save()

            # Enviar correo de confirmación
            try:
                send_mail(
                    subject="Confirmación de Pago",
                    message=f"Hola {request.user.nombre},\n\nTu pago para el plan '{plan.nombre}' por ${monto} fue exitoso. Tu suscripción está extendida hasta {nueva_fecha_fin.strftime('%d/%m/%Y')}.\n\nGracias por confiar en Consultorio Cys.",
                    from_email="soporte@consultoriocys.com",
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                messages.success(request, "El pago fue procesado exitosamente. Se ha enviado un correo de confirmación.")
            except Exception as e:
                messages.error(request, "El pago fue exitoso, pero no se pudo enviar el correo de confirmación.")
            
            return redirect('perfil')
    else:
        form = PagoForm()

    return render(request, 'consultorioCys/procesar_pago.html', {
        'form': form,
        'plan': plan,
        'monto': monto,
        'nueva_fecha_fin': nueva_fecha_fin,
    })
def historial_transacciones(request):
    if not request.user.is_authenticated:
        return redirect('login')

    transacciones = Transaccion.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'consultorioCys/historial_transacciones.html', {'transacciones': transacciones})

def renovar_suscripcion_vencida(request, rut):
    try:
        paciente = Paciente.objects.get(rut_paciente=rut)
        planes = Plan.objects.all()

        # Obtener el último plan vencido
        plan_actual = Suscripcion.objects.filter(
            paciente=paciente, fecha_fin__lt=now()
        ).order_by('-fecha_fin').first()

        if request.method == 'POST':
            plan_id = request.POST.get('plan_id')
            metodo_pago = request.POST.get('metodo_pago')
            plan_seleccionado = Plan.objects.get(id_plan=plan_id)

            # Crear la nueva suscripción
            Suscripcion.objects.create(
                paciente=paciente,
                plan=plan_seleccionado,
                fecha_inicio=now(),
                fecha_fin=now() + timedelta(days=30),
            )

            # Simulación de flujo de pago (integración real opcional)
            if metodo_pago == 'paypal':
                messages.success(request, f"Redirigiendo a PayPal para pagar el plan {plan_seleccionado.nombre}.")
                return redirect('inicio')  # Aquí se redirigiría al flujo de pago real.
            else:
                messages.success(request, f"Suscripción renovada exitosamente con el plan {plan_seleccionado.nombre}.")
                return redirect('inicio')

        return render(request, 'consultorioCys/renovar_suscripcion_vencida.html', {
            'paciente': paciente,
            'planes': planes,
            'plan_actual': plan_actual,
        })

    except Paciente.DoesNotExist:
        messages.error(request, 'El RUT ingresado no corresponde a un paciente válido.')
        return redirect('login')