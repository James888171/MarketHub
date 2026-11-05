from django import forms
from .models import Usuario


class FormularioIngresar(forms.Form):
    email = forms.EmailField(label='Email')


class FormularioRegistro(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=255)
    email = forms.EmailField(label='Email')
    calle = forms.CharField(label='Calle (opcional)', max_length=255, required=False)
    ciudad = forms.CharField(label='Ciudad (opcional)', max_length=255, required=False)


class FormularioUsuario(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=255)
    rol = forms.ChoiceField(label='Rol', choices=Usuario.ROL_CHOICES)
    calle = forms.CharField(label='Calle', max_length=255, required=False)
    ciudad = forms.CharField(label='Ciudad', max_length=255, required=False)
    activo = forms.BooleanField(label='Activo', required=False)
