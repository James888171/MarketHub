from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.producto_listar, name='producto_listar'),
    path('nuevo/', views.producto_crear, name='producto_crear'),
    path('<int:id>/editar/', views.producto_editar, name='producto_editar'),
    path('<int:id>/desactivar/', views.producto_desactivar, name='producto_desactivar'),
    path('catalogo/', views.catalogo, name='catalogo'),
]