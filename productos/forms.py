from django import forms


class FormularioProducto(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=255)
    precio = forms.IntegerField(label='Precio', min_value=1)
    stock = forms.IntegerField(label='Stock', min_value=0)
    activo = forms.BooleanField(label='Activo', required=False)
