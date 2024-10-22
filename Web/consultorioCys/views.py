from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from .models import Doctor, Paciente, Informe, Usuario
from django.contrib.auth.models import Group
from .forms import RUTAuthenticationForm
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.http import JsonResponse
from .models import Paciente, Informe, Cita
from .forms import PacienteForm, CitaForm
from .forms import InformeForm




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

def historial_personal(request):
    return render(request, 'consultorioCys/historial_personal.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .models import Usuario, Paciente, Doctor

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

def buscar_paciente(request):
    if request.method == 'POST':
        # Obtener el RUT ingresado en el formulario
        rut = request.POST.get('rut')

        # Buscar el paciente en la base de datos por su RUT
        try:
            paciente = Paciente.objects.get(rut_paciente=rut)
        except Paciente.DoesNotExist:
            # Si el paciente no existe, mostrar un mensaje de error
            return render(request, 'paciente_no_encontrado.html', {'rut': rut})

        # Si se encuentra el paciente, mostrar sus datos en una plantilla
        return render(request, 'informe_paciente.html', {'paciente': paciente})
    return render(request, 'inicio.html')

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

from django.shortcuts import render, get_object_or_404, redirect
from .models import Paciente, Informe
from .forms import InformeForm

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

@login_required
def agendar_cita(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.paciente = paciente
            cita.save()
            # Usar el framework de mensajes para mostrar confirmación
            messages.success(request, 'Cita agendada con éxito')
            return redirect('inicio')  # Redirigir al inicio después de agendar la cita
    else:
        form = CitaForm()

    return render(request, 'agendar_cita.html', {'form': form, 'paciente': paciente})

def calendario_citas(request):
    # Filtrar citas por el doctor autenticado
    citas = Cita.objects.filter(doctor=request.user.doctor)
    return render(request, 'calendario_citas.html', {'citas': citas})


#ACA TERMINA EL CALENDARIO 
