from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('categorias/', views.categoria_listar, name='categoria_listar'),
    path('categorias/nueva/', views.categoria_crear, name='categoria_crear'),
    path('categorias/<int:id>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:id>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
]