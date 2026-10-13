from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.ingresar, name='ingresar'),
    path('registro/', views.registrarse, name='registrarse'),
    path('salir/', views.salir, name='salir'),
    path('usuarios/', views.usuario_listar, name='usuario_listar'),
    path('usuarios/<int:id>/', views.usuario_detalle, name='usuario_detalle'),
    path('usuarios/<int:id>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:id>/desactivar/', views.usuario_desactivar, name='usuario_desactivar'),
]
