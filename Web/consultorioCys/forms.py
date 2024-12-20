from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Doctor, Paciente, Informe, Cita, MetodoPago
from django.utils.timezone import now

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
    rut = forms.CharField(max_length=10, label="RUT")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

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
    
from django import forms
from .models import Informe

class InformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        exclude = ['doctor', 'paciente']
        widgets = {
            'titulo_informe': forms.TextInput(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Ingrese un título descriptivo',
            }),
            'descripcion_informe': forms.Textarea(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Describa los detalles relevantes del informe',
                'rows': 4,
            }),
            'notas_doctor': forms.Textarea(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Añada notas o comentarios importantes',
                'rows': 4,
            }),
            'instrucciones_tratamiento': forms.Textarea(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Escriba las instrucciones de tratamiento',
                'rows': 3,
            }),
            'documentos_extra': forms.ClearableFileInput(attrs={
                'class': 'form-control mb-3',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.label_suffix = ""  # Eliminar los dos puntos (:) después de las etiquetas


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['rut_paciente', 'nombres_paciente', 'primer_apellido_paciente', 'segundo_apellido_paciente', 'correo_paciente', 'telefono_paciente', 'fecha_nacimiento_paciente', 'direccion_paciente', 'genero_paciente', 'archivo']

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['fecha_cita', 'hora_cita', 'motivo_consulta']
        widgets = {
            'fecha_cita': forms.DateInput(attrs={'type': 'date'}),
            'hora_cita': forms.TimeInput(attrs={'type': 'time'}),
            'motivo_consulta': forms.TextInput(attrs={'placeholder': 'Motivo de la consulta'}),
        }

class PagoForm(forms.Form):
    tarjeta_numero = forms.CharField(max_length=16, min_length=16, label="Número de Tarjeta")
    tarjeta_tipo = forms.ChoiceField(choices=[('Visa', 'Visa'), ('Mastercard', 'Mastercard')], label="Tipo de Tarjeta")
    vencimiento_mes = forms.ChoiceField(choices=[(str(i), f"{i:02d}") for i in range(1, 13)], label="Mes de Vencimiento")
    vencimiento_anio = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(now().year, now().year + 10)], label="Año de Vencimiento")
    cvv = forms.CharField(max_length=3, min_length=3, label="CVV", widget=forms.PasswordInput)

class MetodoPagoForm(forms.ModelForm):
    class Meta:
        model = MetodoPago
        fields = ['tarjeta_tipo', 'tarjeta_numero', 'vencimiento']
        widgets = {
            'tarjeta_tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ejemplo: Visa'}),
            'tarjeta_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Últimos 4 dígitos'}),
            'vencimiento': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'MM/AAAA', 'type': 'date'}),
        }

class InformeExternoForm(forms.ModelForm):
    rut_doctor = forms.CharField(max_length=10, required=True, label="RUT del Doctor")  # Campo para RUT del doctor
    nombre_doctor = forms.CharField(max_length=255, required=True, label="Nombre del Doctor")  # Campo para nombre del doctor

    class Meta:
        model = Informe
        fields = ['titulo_informe', 'documentos_extra']  # Campos existentes que se van a usar
        labels = {
            'titulo_informe': 'Título del Informe',
            'documentos_extra': 'Documento Adjunto',
        }