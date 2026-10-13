from django.urls import path
from . import views

app_name = 'categorias'

urlpatterns = [
    path('', views.categoria_listar, name='categoria_listar'),
    path('nueva/', views.categoria_crear, name='categoria_crear'),
    path('<int:id>/editar/', views.categoria_editar, name='categoria_editar'),
    path('<int:id>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
]
