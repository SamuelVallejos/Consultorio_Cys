from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Doctor


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

    class Meta:
        model = User
        fields = ['username', 'email', 'is_doctor']

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
            is_doctor = self.cleaned_data['is_doctor']
            if is_doctor:
                group = Group.objects.get(name='Doctor')
            else:
                group = Group.objects.get(name='Usuario')

            user.groups.add(group)  # Añadir el usuario al grupo
        return user

class AddDoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['nombre_completo', 'area_desempeño', 'fec_nac', 'num_telefono', 'sitio']