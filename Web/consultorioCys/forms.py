from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Doctor, Paciente, Informe

class CustomUserEditForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100, required=False, label="Nombre Completo")
    phone = forms.CharField(max_length=15, required=False, label="Teléfono")
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone']
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise ValidationError("El número de teléfono debe contener solo dígitos.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data['full_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput)
    is_doctor = forms.BooleanField(required=False, label='¿Es doctor?')
    is_admin = forms.BooleanField(required=False, label='¿Es administrador?')

    class Meta:
        model = User
        fields = ['username', 'email', 'is_doctor', 'is_admin']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

            # Asignar al grupo correspondiente
            if self.cleaned_data['is_doctor']:
                group = Group.objects.get(name='Doctor')
            elif self.cleaned_data['is_admin']:
                group = Group.objects.get(name='Administrador')
            else:
                group = Group.objects.get(name='Paciente')

            user.groups.add(group)
        return user

class AddDoctorForm(forms.ModelForm):
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
            'especialidad_doctor'
        ]

class AddPacienteForm(forms.ModelForm):
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
            'genero_paciente'
        ]

# La clase AddAdministradorForm ha sido eliminada

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