from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserEditForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100, required=False, label="Nombre Completo")  # Campo adicional opcional
    phone = forms.CharField(max_length=15, required=False , label="Teléfono")  # Campo adicional opcional
    email = forms.EmailField(label="Correo electrónico")


    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone']
        labels = {
            'username': 'Nombre de usuario',
        }
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

    class Meta:
        model = User
        fields = ['username', 'email']

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
        return user
