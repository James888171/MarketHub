from django.urls import path
from . import views

app_name = 'ordenes'

urlpatterns = [
    path('carrito/', views.carrito_ver, name='carrito_ver'),
    path('carrito/agregar/', views.carrito_agregar, name='carrito_agregar'),
    path('carrito/actualizar/', views.carrito_actualizar, name='carrito_actualizar'),
    path('carrito/quitar/<int:posicion>/', views.carrito_quitar, name='carrito_quitar'),
    path('carrito/finalizar/', views.carrito_finalizar, name='carrito_finalizar'),
    path('', views.orden_listar, name='orden_listar'),
    path('<int:id>/', views.orden_detalle, name='orden_detalle'),
    path('<int:id>/estado/', views.orden_cambiar_estado, name='orden_cambiar_estado'),
    path('<int:id>/cancelar/', views.orden_cancelar, name='orden_cancelar'),
]
