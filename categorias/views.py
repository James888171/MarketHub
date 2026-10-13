from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render, redirect
from usuarios.views import usuario_actual
from .models import Categoria


def categoria_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
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
    if usuario['rol'] != 'admin':
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
            Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                activo=activo,
            )
            return redirect('categorias:categoria_listar')

        categoria = {'nombre': nombre, 'descripcion': descripcion, 'activo': activo}

    contexto = {
        'categoria': categoria,
        'error': error,
        'titulo': 'Nueva categoría',
        'boton': 'Crear categoría',
    }
    return render(request, 'categorias/categoria_form.html', contexto)


def categoria_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
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
            categoria.save()
            return redirect('categorias:categoria_listar')

    contexto = {
        'categoria': categoria,
        'error': error,
        'titulo': 'Editar categoría',
        'boton': 'Guardar cambios',
    }
    return render(request, 'categorias/categoria_form.html', contexto)


def categoria_eliminar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('ordenes:carrito_ver')

    try:
        categoria = Categoria.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('categorias:categoria_listar')

    if request.method == 'POST':
        categoria.delete()
        return redirect('categorias:categoria_listar')

    return render(request, 'categorias/categoria_eliminar.html', {'categoria': categoria})
