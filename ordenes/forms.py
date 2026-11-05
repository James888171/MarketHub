from django import forms


class FormularioDireccion(forms.Form):
    calle = forms.CharField(label='Calle', max_length=255)
    ciudad = forms.CharField(label='Ciudad', max_length=255)
