from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from .models import Doctor, Paciente
from django.contrib.auth.models import Group
from .forms import RUTAuthenticationForm
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm

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
    return render(request, 'consultorioCys/inicio.html')

def ia(request):
    return render(request, 'consultorioCys/ia.html')

def historial_personal(request):
    return render(request, 'consultorioCys/historial_personal.html')

def historial(request):
    return render(request, 'consultorioCys/historial.html')

def perfil_view(request):
    return render(request, 'consultorioCys/perfil.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            print("Redirigiendo a superusuario...")
            return redirect('/inicio/')  # Redirigir al inicio si es superusuario
        else:
            messages.info(request, "Ya has iniciado sesión.")
            print("Redirigiendo a inicio por sesión activa...")
            return redirect('inicio')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data.get('rut')
            password = form.cleaned_data.get('password')

            print(f"RUT ingresado: {rut}")
            print(f"Contraseña ingresada: {password}")
            print(f"Datos POST: {request.POST}")

            # Intentar autenticar al doctor
            try:
                doctor = Doctor.objects.get(rut_doctor=rut)
                if doctor.check_password(password):
                    print(f"Doctor encontrado: {doctor}")
                    print(f"Datos del Doctor: {doctor.__dict__}")

                    # Guardar RUT del doctor en la sesión
                    request.session['doctor_rut'] = doctor.rut_doctor
                    print("Redirigiendo al dashboard del doctor...")
                    return redirect('doctor_dashboard')  # Redirigir al dashboard del doctor
                else:
                    messages.error(request, 'Contraseña incorrecta para el doctor.')
                    print("Contraseña incorrecta para el doctor.")
            except Doctor.DoesNotExist:
                # Si no existe el doctor, buscar al paciente
                try:
                    paciente = Paciente.objects.get(rut_paciente=rut)
                    if paciente.check_password(password):
                        print(f"Paciente encontrado: {paciente}")
                        print(f"Datos del Paciente: {paciente.__dict__}")

                        # Guardar RUT del paciente en la sesión
                        request.session['paciente_rut'] = paciente.rut_paciente
                        print("Redirigiendo al dashboard del paciente...")
                        return redirect('inicio')  # Redirigir al dashboard del paciente
                    else:
                        messages.error(request, 'Contraseña incorrecta para el paciente.')
                        print("Contraseña incorrecta para el paciente.")
                except Paciente.DoesNotExist:
                    messages.error(request, 'RUT no registrado.')
                    print("RUT no registrado.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

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
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
def paciente_dashboard(request):
    return render(request, 'consultorioCys/paciente_dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# Función auxiliar para verificar si es usuario
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