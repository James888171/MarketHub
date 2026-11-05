from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('categorias/', include('categorias.urls')),
    path('productos/', include('productos.urls')),
    path('ordenes/', include('ordenes.urls')),
]