from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .models import Doctor
from .models import Paciente
from .forms import RUTAuthenticationForm, LoginForm
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt

def inicio(request):
    return render(request, 'consultorioCys/inicio.html')

def ia(request):
    return render(request, 'consultorioCys/ia.html')

def historial_personal(request):
    return render(request, 'consultorioCys/historial_personal.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil_view(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')

    if user_type == 'doctor':
        doctor = Doctor.objects.get(rut_doctor=user_id)
        context = {
            'nombres': doctor.nombres_doctor,
            'apellido': doctor.primer_apellido_doctor,
            'correo': doctor.correo_doctor,
            'telefono': doctor.telefono_doctor,
            'especialidad': doctor.especialidad_doctor,
        }
    elif user_type == 'paciente':
        paciente = Paciente.objects.get(rut_paciente=user_id)
        context = {
            'nombres': paciente.nombres_paciente,
            'apellido': paciente.primer_apellido_paciente,
            'correo': paciente.correo_paciente,
            'telefono': paciente.telefono_paciente,
        }
    else:
        # Manejar el caso donde no hay sesión activa
        messages.error(request, 'No hay sesión activa')
        return redirect('login')  # Redirigir a la página de login

    return render(request, 'perfil.html', context)


# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Doctor, Paciente
from .forms import LoginForm

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Doctor, Paciente
from .forms import LoginForm

from consultorioCys.models import Doctor, Paciente
doctor = Doctor.objects.filter(rut_doctor='RUT_DEL_DOCTOR').first()
print(doctor)  # Esto debería imprimir los detalles del doctor si existe
paciente = Paciente.objects.filter(rut_paciente='RUT_DEL_PACIENTE').first()
print(paciente)  # Esto debería imprimir los detalles del paciente si existe

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data['rut']
            password = form.cleaned_data['password']
            
            # Intenta encontrar al doctor
            try:
                doctor = Doctor.objects.get(rut_doctor=rut)
                if doctor.check_password(password):
                    login(request, doctor)  # Esto autentica al doctor
                    return redirect('doctor_dashboard')
            except Doctor.DoesNotExist:
                # Intenta encontrar al paciente
                try:
                    paciente = Paciente.objects.get(rut_paciente=rut)
                    if paciente.check_password(password):
                        login(request, paciente)  # Esto autentica al paciente
                        return redirect('paciente_dashboard')
                except Paciente.DoesNotExist:
                    messages.error(request, 'El RUT no existe en la base de datos')
    
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Doctor').exists())
def doctor_dashboard(request):
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Paciente').exists())
def paciente_dashboard(request):
    return render(request, 'consultorioCys/paciente_dashboard.html')

def logout_view(request):
    request.session.flush()  # Limpia la sesión
    return redirect('login')

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

def is_usuario(user):
    return user.groups.filter(name='Usuario').exists()

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    # Lógica específica para doctores
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
@user_passes_test(is_usuario)
def usuario_dashboard(request):
    # Lógica específica para usuarios normales
    return render(request, 'consultorioCys/inicio.html')

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

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Paciente').exists())
def paciente_dashboard(request):
    # Lógica específica para pacientes
    return render(request, 'consultorioCys/paciente_dashboard.html')


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
        return render(request, 'detalle_paciente.html', {'paciente': paciente})
    return render(request, 'inicio.html')

def login_doctor(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')  # Obtener el RUT del formulario
        password = request.POST.get('contrasena_doctor')  # Obtener la contraseña

        # Verificar la existencia del doctor
        doctor = get_object_or_404(Doctor, rut_doctor=rut)
        
        # Verificar la contraseña
        if doctor.check_password(password):
            # Iniciar sesión
            auth_login(request, doctor)
            return redirect('doctor_dashboard')
        else:
            messages.error(request, 'Contraseña incorrecta.')

    return render(request, 'consultorioCys/login_doctor.html')

def listar_pacientes(request):
    pacientes = Paciente.objects.all()  # Obtener todos los pacientes
    return render(request, 'consultorioCys/pacientes_list.html', {'pacientes': pacientes})

# Vista para eliminar paciente
def eliminar_paciente(request, rut_paciente):
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)
    
    if request.method == 'POST':
        paciente.delete()
        messages.success(request, 'Paciente eliminado correctamente.')
        return redirect('listar_pacientes')

    return render(request, 'consultorioCys/confirmar_borrar.html', {'paciente': paciente})

# Vista para editar paciente (redirección simulada)
def editar_paciente(request, rut_paciente):
    # Simulación de redirección a una página de edición de paciente
    # Solo redirige a una página con mensaje (para completar según necesidad)
    messages.info(request, f"Redirigido para editar paciente con RUT: {rut_paciente}")
    return redirect('listar_pacientes')