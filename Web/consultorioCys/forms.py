from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Doctor, Paciente, Informe

class RUTAuthenticationForm(forms.Form):
    rut = forms.CharField(label="RUT", max_length=10)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def clean(self):
        rut = self.cleaned_data.get('rut')
        password = self.cleaned_data.get('password')
        
        print(f"RUT: {rut}, Contraseña: {password}")

        # Intentar autenticar como doctor
        try:
            doctor = Doctor.objects.get(rut_doctor=rut)
            if doctor.check_password(password):  # Verifica la contraseña con hash
                self.user_cache = doctor
        except Doctor.DoesNotExist:
            pass

        # Si no es doctor, intentar autenticar como paciente
        if self.user_cache is None:
            try:
                paciente = Paciente.objects.get(rut_paciente=rut)
                if paciente.check_password(password):  # Verifica la contraseña
                    self.user_cache = paciente
            except Paciente.DoesNotExist:
                pass

        if self.user_cache is None:
            raise ValidationError("RUT o contraseña incorrectos.")
        
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

class LoginForm(forms.Form):
    rut = forms.CharField(label='RUT', max_length=10)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class AddPacienteForm(forms.ModelForm):
    contrasena_paciente = forms.CharField(widget=forms.PasswordInput, label='Contraseña')

    class Meta:
        model = Paciente
        fields = [
            'rut_paciente', 
            'nombres_paciente', 
            'primer_apellido_paciente', 
            'segundo_apellido_paciente', 
            'correo_paciente', 
            'telefono_paciente', 
            'fecha_nacimiento_paciente', 
            'direccion_paciente', 
            'genero_paciente',
            'contrasena_paciente'
        ]

    def save(self, commit=True):
        paciente_instance = super().save(commit=False)  # Cambié el nombre aquí
        paciente_instance.set_password(self.cleaned_data['contrasena_paciente'])  # Asegúrate de usar set_password
        if commit:
            paciente_instance.save()
        return paciente_instance

class AddDoctorForm(forms.ModelForm):
    contrasena_doctor = forms.CharField(widget=forms.PasswordInput, label='Contraseña')

    class Meta:
        model = Doctor
        fields = [
            'rut_doctor', 
            'nombres_doctor', 
            'primer_apellido_doctor', 
            'segundo_apellido_doctor', 
            'correo_doctor', 
            'telefono_doctor', 
            'fecha_nacimiento_doctor', 
            'especialidad_doctor',
            'contrasena_doctor'  # Incluir el campo de contraseña
        ]

    def save(self, commit=True):
        doctor_instance = super().save(commit=False)  # Cambié el nombre aquí
        doctor_instance.set_password(self.cleaned_data['contrasena_doctor'])  # Asegúrate de usar set_password
        if commit:
            doctor_instance.save()
        return doctor_instance

class AddInformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        fields = [
            'doctor', 
            'paciente', 
            'titulo_informe', 
            'descripcion_informe', 
            'notas_doctor', 
            'instrucciones_tratamiento', 
            'documentos_extra'
        ]