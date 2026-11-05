from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.shortcuts import render, redirect
from categorias.models import Categoria
from usuarios.views import usuario_actual
from .forms import FormularioProducto
from .models import Producto


def categorias_activas():
    lista = []
    for categoria in Categoria.objects.order_by('nombre'):
        if categoria.activo:
            lista.append(categoria)
    return lista


def buscar_categoria(categoria_id):
    if not categoria_id.isdigit():
        return None
    try:
        return Categoria.objects.get(id=int(categoria_id))
    except ObjectDoesNotExist:
        return None


def producto_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')

    productos = Producto.objects.all()
    if busqueda:
        productos = productos.filter(nombre=busqueda)
    categoria = buscar_categoria(categoria_id)
    if categoria:
        productos = productos.filter(categoria={'categoria_id': categoria.id})
    productos = productos.order_by('nombre')

    contexto = {
        'productos': productos,
        'categorias': Categoria.objects.order_by('nombre'),
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'total': Producto.objects.count(),
    }
    return render(request, 'productos/producto_lista.html', contexto)


def producto_crear(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    error = None
    producto = {'nombre': '', 'precio': '', 'stock': '', 'categoria_id': '', 'activo': True}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        categoria_id = request.POST.get('categoria', '')
        activo = request.POST.get('activo') == 'on'
        producto = {'nombre': nombre, 'precio': precio, 'stock': stock, 'categoria_id': categoria_id, 'activo': activo}

        categoria = buscar_categoria(categoria_id)

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif not precio.isdigit() or int(precio) == 0:
            error = 'El precio debe ser un numero mayor a 0.'
        elif not stock.isdigit():
            error = 'El stock debe ser un numero.'
        elif not categoria:
            error = 'Debes seleccionar una categoria.'
        elif Producto.objects.filter(nombre=nombre).first():
            error = 'Ya existe un producto con ese nombre.'
        else:
            try:
                Producto.objects.create(
                    nombre=nombre,
                    precio=int(precio),
                    stock=int(stock),
                    categoria={
                        'categoria_id': categoria.id,
                        'nombre': categoria.nombre,
                        'descripcion': categoria.descripcion,
                    },
                    activo=activo,
                )
                return redirect('productos:producto_listar')
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

    contexto = {
        'formulario': FormularioProducto(initial=producto),
        'producto': producto,
        'categorias': categorias_activas(),
        'error': error,
        'titulo': 'Nuevo producto',
        'boton': 'Crear producto',
    }
    return render(request, 'productos/producto_form.html', contexto)


def producto_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        original = Producto.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('productos:producto_listar')

    error = None

    producto = {
        'nombre': original.nombre,
        'precio': original.precio,
        'stock': original.stock,
        'categoria_id': str(original.categoria['categoria_id']),
        'activo': original.activo,
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        categoria_id = request.POST.get('categoria', '')
        activo = request.POST.get('activo') == 'on'
        producto = {'nombre': nombre, 'precio': precio, 'stock': stock, 'categoria_id': categoria_id, 'activo': activo}

        categoria = buscar_categoria(categoria_id)
        repetido = Producto.objects.filter(nombre=nombre).first()

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif not precio.isdigit() or int(precio) == 0:
            error = 'El precio debe ser un numero mayor a 0.'
        elif not stock.isdigit():
            error = 'El stock debe ser un numero.'
        elif not categoria:
            error = 'Debes seleccionar una categoria.'
        elif repetido and repetido.id != id:
            error = 'Ya existe otro producto con ese nombre.'
        else:
            original.nombre = nombre
            original.precio = int(precio)
            original.stock = int(stock)
            original.categoria = {
                'categoria_id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion,
            }
            original.activo = activo

            try:
                original.save()
                return redirect('productos:producto_listar')
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

    contexto = {
        'formulario': FormularioProducto(initial=producto),
        'producto': producto,
        'categorias': categorias_activas(),
        'error': error,
        'titulo': 'Editar producto',
        'boton': 'Guardar cambios',
    }
    return render(request, 'productos/producto_form.html', contexto)


def producto_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        producto = Producto.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('productos:producto_listar')

    return render(request, 'productos/producto_detalle.html', {'producto': producto})


def producto_desactivar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        producto = Producto.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('productos:producto_listar')

    if request.method == 'POST':
        producto.activo = False
        producto.save()
        return redirect('productos:producto_listar')

    return render(request, 'productos/producto_desactivar.html', {'producto': producto})


def catalogo(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    categoria_id = request.GET.get('categoria', '')

    todos = Producto.objects.all()
    categoria = buscar_categoria(categoria_id)
    if categoria:
        todos = todos.filter(categoria={'categoria_id': categoria.id})
    todos = todos.order_by('nombre')

    productos = []
    for producto in todos:
        if producto.activo:
            productos.append(producto)

    contexto = {
        'productos': productos,
        'categorias': categorias_activas(),
        'categoria_id': categoria_id,
    }
    return render(request, 'productos/catalogo.html', contexto)
