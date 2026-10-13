from django.shortcuts import render, redirect
from MarketHub.conexion import db, siguiente_id
from usuarios.views import usuario_actual


def producto_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')

    filtro = {}
    if busqueda:
        filtro['nombre'] = busqueda
    if categoria_id.isdigit():
        categoria = db.categorias.find_one({'id': int(categoria_id)})
        if categoria:
            filtro['categoria._id'] = categoria['_id']

    productos = list(db.productos.find(filtro).sort('nombre', 1))
    categorias = list(db.categorias.find().sort('nombre', 1))

    contexto = {
        'productos': productos,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'total': db.productos.count_documents({}),
    }
    return render(request, 'productos/producto_lista.html', contexto)


def producto_crear(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    error = None
    producto = {'nombre': '', 'precio': '', 'stock': '', 'categoria_id': '', 'activo': True}
    categorias = list(db.categorias.find({'activo': True}).sort('nombre', 1))

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        categoria_id = request.POST.get('categoria', '')
        activo = request.POST.get('activo') == 'on'
        producto = {'nombre': nombre, 'precio': precio, 'stock': stock, 'categoria_id': categoria_id, 'activo': activo}

        categoria = None
        if categoria_id.isdigit():
            categoria = db.categorias.find_one({'id': int(categoria_id)})

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif not precio.isdigit() or int(precio) == 0:
            error = 'El precio debe ser un numero mayor a 0.'
        elif not stock.isdigit():
            error = 'El stock debe ser un numero.'
        elif not categoria:
            error = 'Debes seleccionar una categoria.'
        elif db.productos.find_one({'nombre': nombre}):
            error = 'Ya existe un producto con ese nombre.'
        else:
            db.productos.insert_one({
                'id': siguiente_id(db.productos),
                'nombre': nombre,
                'precio': int(precio),
                'stock': int(stock),
                'categoria': {
                    '_id': categoria['_id'],
                    'nombre': categoria['nombre'],
                    'descripcion': categoria.get('descripcion'),
                },
                'activo': activo,
            })
            return redirect('productos:producto_listar')

    contexto = {
        'producto': producto,
        'categorias': categorias,
        'error': error,
        'titulo': 'Nuevo producto',
        'boton': 'Crear producto',
    }
    return render(request, 'productos/producto_form.html', contexto)


def producto_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    original = db.productos.find_one({'id': id})
    if not original:
        return redirect('productos:producto_listar')

    error = None
    categorias = list(db.categorias.find({'activo': True}).sort('nombre', 1))

    categoria_id = ''
    for c in db.categorias.find():
        if c['_id'] == original['categoria']['_id']:
            categoria_id = str(c['id'])

    producto = {
        'nombre': original['nombre'],
        'precio': original['precio'],
        'stock': original['stock'],
        'categoria_id': categoria_id,
        'activo': original['activo'],
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        categoria_id = request.POST.get('categoria', '')
        activo = request.POST.get('activo') == 'on'
        producto = {'nombre': nombre, 'precio': precio, 'stock': stock, 'categoria_id': categoria_id, 'activo': activo}

        categoria = None
        if categoria_id.isdigit():
            categoria = db.categorias.find_one({'id': int(categoria_id)})

        repetido = db.productos.find_one({'nombre': nombre})

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif not precio.isdigit() or int(precio) == 0:
            error = 'El precio debe ser un numero mayor a 0.'
        elif not stock.isdigit():
            error = 'El stock debe ser un numero.'
        elif not categoria:
            error = 'Debes seleccionar una categoria.'
        elif repetido and repetido['id'] != id:
            error = 'Ya existe otro producto con ese nombre.'
        else:
            db.productos.update_one(
                {'id': id},
                {'$set': {
                    'nombre': nombre,
                    'precio': int(precio),
                    'stock': int(stock),
                    'categoria': {
                        '_id': categoria['_id'],
                        'nombre': categoria['nombre'],
                        'descripcion': categoria.get('descripcion'),
                    },
                    'activo': activo,
                }}
            )
            return redirect('productos:producto_listar')

    contexto = {
        'producto': producto,
        'categorias': categorias,
        'error': error,
        'titulo': 'Editar producto',
        'boton': 'Guardar cambios',
    }
    return render(request, 'productos/producto_form.html', contexto)


def producto_desactivar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    producto = db.productos.find_one({'id': id})
    if not producto:
        return redirect('productos:producto_listar')

    if request.method == 'POST':
        db.productos.update_one({'id': id}, {'$set': {'activo': False}})
        return redirect('productos:producto_listar')

    return render(request, 'productos/producto_desactivar.html', {'producto': producto})


def catalogo(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    categoria_id = request.GET.get('categoria', '')

    filtro = {'activo': True}
    if categoria_id.isdigit():
        categoria = db.categorias.find_one({'id': int(categoria_id)})
        if categoria:
            filtro['categoria._id'] = categoria['_id']

    productos = list(db.productos.find(filtro).sort('nombre', 1))
    categorias = list(db.categorias.find({'activo': True}).sort('nombre', 1))

    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_id': categoria_id,
    }
    return render(request, 'productos/catalogo.html', contexto)