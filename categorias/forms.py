from django import forms


class FormularioCategoria(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=255)
    descripcion = forms.CharField(label='Descripcion', max_length=255, required=False)
    activo = forms.BooleanField(label='Activa', required=False)
