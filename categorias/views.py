from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import render, redirect
from productos.models import Producto
from usuarios.views import usuario_actual
from .forms import FormularioCategoria
from .models import Categoria


def categoria_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    busqueda = request.GET.get('q', '').strip()

    categorias = Categoria.objects.all()
    if busqueda:
        categorias = categorias.filter(
            Q(nombre=busqueda) | Q(descripcion=busqueda)
        )
    categorias = categorias.order_by('nombre')

    contexto = {
        'categorias': categorias,
        'busqueda': busqueda,
        'total': Categoria.objects.count(),
    }
    return render(request, 'categorias/categoria_lista.html', contexto)


def categoria_crear(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    error = None
    categoria = {'activo': True}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('activo') == 'on'

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif Categoria.objects.filter(nombre=nombre).exists():
            error = 'Ya existe una categoría con ese nombre.'
        else:
            try:
                Categoria.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    activo=activo,
                )
                return redirect('categorias:categoria_listar')
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

        categoria = {'nombre': nombre, 'descripcion': descripcion, 'activo': activo}

    contexto = {
        'formulario': FormularioCategoria(initial=categoria),
        'error': error,
    }
    return render(request, 'categorias/categoria_crear.html', contexto)


def categoria_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    try:
        categoria = Categoria.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('categorias:categoria_listar')

    error = None

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('activo') == 'on'

        categoria.nombre = nombre
        categoria.descripcion = descripcion
        categoria.activo = activo

        repetida = Categoria.objects.filter(nombre=nombre).first()

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif repetida and repetida.id != categoria.id:
            error = 'Ya existe otra categoría con ese nombre.'
        else:
            try:
                categoria.save()
                for producto in Producto.objects.filter(categoria={'categoria_id': categoria.id}):
                    producto.categoria = {
                        'categoria_id': categoria.id,
                        'nombre': categoria.nombre,
                        'descripcion': categoria.descripcion,
                    }
                    producto.save()
                return redirect('categorias:categoria_listar')
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

    datos = {
        'nombre': categoria.nombre,
        'descripcion': categoria.descripcion,
        'activo': categoria.activo,
    }

    contexto = {
        'formulario': FormularioCategoria(initial=datos),
        'error': error,
    }
    return render(request, 'categorias/categoria_editar.html', contexto)


def categoria_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    try:
        categoria = Categoria.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('categorias:categoria_listar')

    return render(request, 'categorias/categoria_detalle.html', {'categoria': categoria})


def categoria_desactivar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    try:
        categoria = Categoria.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('categorias:categoria_listar')

    if request.method == 'POST':
        categoria.activo = False
        categoria.save()
        return redirect('categorias:categoria_listar')

    return render(request, 'categorias/categoria_desactivar.html', {'categoria': categoria})


def categoria_eliminar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    try:
        categoria = Categoria.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('categorias:categoria_listar')

    error = None
    if Producto.objects.filter(categoria={'categoria_id': categoria.id}).first():
        error = 'No se puede eliminar porque hay productos con esta categoria. Puedes desactivarla.'

    if request.method == 'POST' and not error:
        categoria.delete()
        return redirect('categorias:categoria_listar')

    return render(request, 'categorias/categoria_eliminar.html', {'categoria': categoria, 'error': error})
