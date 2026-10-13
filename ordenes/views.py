from datetime import datetime

from django.shortcuts import render, redirect
from MarketHub.conexion import db, siguiente_id
from usuarios.views import usuario_actual
from .models import Orden


def nombre_estado(estado):
    for valor, nombre in Orden.ESTADOS:
        if valor == estado:
            return nombre
    return estado


def estado_valido(estado):
    for valor, nombre in Orden.ESTADOS:
        if valor == estado:
            return True
    return False


def se_puede_cancelar(orden):
    return orden['estado'] == 'pendiente' or orden['estado'] == 'pagado'


def obtener_carrito(usuario):
    carrito = db.carritocompras.find_one({'usuario._id': usuario['_id']})
    if not carrito:
        carrito = {
            'id': siguiente_id(db.carritocompras),
            'usuario': {
                '_id': usuario['_id'],
                'email': usuario['email'],
                'nombre': usuario['nombre'],
            },
            'items': [],
            'actualizado_en': datetime.now(),
        }
        db.carritocompras.insert_one(carrito)
    return carrito


def guardar_items(carrito, items):
    db.carritocompras.update_one(
        {'_id': carrito['_id']},
        {'$set': {'items': items, 'actualizado_en': datetime.now()}}
    )


def devolver_stock(orden):
    for item in orden['items']:
        db.productos.update_one(
            {'_id': item['producto']['_id']},
            {'$inc': {'stock': item['cantidad']}}
        )


def mostrar_carrito(request, usuario, error):
    carrito = obtener_carrito(usuario)

    total = 0
    for item in carrito['items']:
        item['subtotal'] = item['producto']['precio'] * item['cantidad']
        total = total + item['subtotal']

    direccion = {}
    if usuario.get('direccion'):
        direccion = usuario['direccion']

    contexto = {
        'carrito': carrito,
        'total': total,
        'direccion': direccion,
        'error': error,
    }
    return render(request, 'ordenes/carrito.html', contexto)


def mostrar_detalle(request, usuario, orden, error):
    orden['estado_nombre'] = nombre_estado(orden['estado'])
    for item in orden['items']:
        item['subtotal'] = item['precio_unitario'] * item['cantidad']

    contexto = {
        'es_admin': usuario['rol'] == 'admin',
        'orden': orden,
        'estados': Orden.ESTADOS,
        'puede_cancelar': se_puede_cancelar(orden),
        'error': error,
    }
    return render(request, 'ordenes/orden_detalle.html', contexto)


def carrito_ver(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    return mostrar_carrito(request, usuario, None)


def carrito_agregar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if request.method != 'POST':
        return redirect('ordenes:carrito_ver')

    producto_id = request.POST.get('producto', '')
    cantidad = request.POST.get('cantidad', '').strip()

    producto = None
    if producto_id.isdigit():
        producto = db.productos.find_one({'id': int(producto_id), 'activo': True})

    if not producto:
        return mostrar_carrito(request, usuario, 'Debes seleccionar un producto.')

    if not cantidad.isdigit() or int(cantidad) == 0:
        return mostrar_carrito(request, usuario, 'La cantidad debe ser un número mayor a 0.')

    cantidad = int(cantidad)
    carrito = obtener_carrito(usuario)
    items = carrito['items']

    encontrado = False
    for item in items:
        if item['producto']['_id'] == producto['_id']:
            item['cantidad'] = item['cantidad'] + cantidad
            cantidad = item['cantidad']
            encontrado = True

    if cantidad > producto['stock']:
        return mostrar_carrito(request, usuario, 'Solo hay ' + str(producto['stock']) + ' unidades de ' + producto['nombre'] + '.')

    if not encontrado:
        items.append({
            'producto': {
                '_id': producto['_id'],
                'nombre': producto['nombre'],
                'precio': producto['precio'],
            },
            'cantidad': cantidad,
        })

    guardar_items(carrito, items)
    return redirect('ordenes:carrito_ver')


def carrito_actualizar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if request.method != 'POST':
        return redirect('ordenes:carrito_ver')

    carrito = obtener_carrito(usuario)
    items = []
    posicion = 0

    for item in carrito['items']:
        cantidad = request.POST.get('cantidad_' + str(posicion), '').strip()
        posicion = posicion + 1

        if not cantidad.isdigit():
            return mostrar_carrito(request, usuario, 'Las cantidades deben ser numeros enteros.')

        cantidad = int(cantidad)
        if cantidad == 0:
            continue

        producto = db.productos.find_one({'_id': item['producto']['_id']})
        if producto and cantidad > producto['stock']:
            return mostrar_carrito(request, usuario, 'Solo hay ' + str(producto['stock']) + ' unidades de ' + producto['nombre'] + '.')

        item['cantidad'] = cantidad
        items.append(item)

    guardar_items(carrito, items)
    return redirect('ordenes:carrito_ver')


def carrito_quitar(request, posicion):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    carrito = obtener_carrito(usuario)
    items = carrito['items']
    if posicion < len(items):
        items.pop(posicion)
        guardar_items(carrito, items)

    return redirect('ordenes:carrito_ver')


def carrito_finalizar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if request.method != 'POST':
        return redirect('ordenes:carrito_ver')

    carrito = obtener_carrito(usuario)
    calle = request.POST.get('calle', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()

    if not carrito['items']:
        return mostrar_carrito(request, usuario, 'El carrito esta vacio.')

    if not calle or not ciudad:
        return mostrar_carrito(request, usuario, 'La direccion de envio esta incompleta.')

    items = []
    total = 0
    for item in carrito['items']:
        producto = db.productos.find_one({'_id': item['producto']['_id']})

        if not producto or not producto['activo']:
            return mostrar_carrito(request, usuario, 'El producto ' + item['producto']['nombre'] + ' ya no esta disponible.')

        if item['cantidad'] > producto['stock']:
            return mostrar_carrito(request, usuario, 'Solo hay ' + str(producto['stock']) + ' unidades de ' + producto['nombre'] + '.')

        items.append({
            'producto': {
                '_id': producto['_id'],
                'nombre': producto['nombre'],
                'precio': producto['precio'],
            },
            'precio_unitario': producto['precio'],
            'cantidad': item['cantidad'],
        })
        total = total + producto['precio'] * item['cantidad']

    orden_id = siguiente_id(db.ordenes)

    db.ordenes.insert_one({
        'id': orden_id,
        'usuario': carrito['usuario'],
        'fecha': datetime.now(),
        'estado': 'pendiente',
        'items': items,
        'total': total,
        'direccion_envio': {'calle': calle, 'ciudad': ciudad},
    })

    for item in items:
        db.productos.update_one(
            {'_id': item['producto']['_id']},
            {'$inc': {'stock': -item['cantidad']}}
        )

    guardar_items(carrito, [])
    return redirect('ordenes:orden_detalle', id=orden_id)


def orden_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    es_admin = usuario['rol'] == 'admin'
    busqueda = request.GET.get('q', '').strip().lower()
    estado = request.GET.get('estado', '')

    filtro = {}
    if not es_admin:
        filtro['usuario._id'] = usuario['_id']
    if estado:
        filtro['estado'] = estado
    if busqueda and es_admin:
        filtro['usuario.email'] = busqueda

    ordenes = list(db.ordenes.find(filtro).sort('fecha', -1))
    for orden in ordenes:
        orden['estado_nombre'] = nombre_estado(orden['estado'])
        orden['cantidad_productos'] = 0
        for item in orden['items']:
            orden['cantidad_productos'] = orden['cantidad_productos'] + item['cantidad']

    contexto = {
        'es_admin': es_admin,
        'ordenes': ordenes,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Orden.ESTADOS,
    }
    return render(request, 'ordenes/orden_lista.html', contexto)


def orden_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    orden = db.ordenes.find_one({'id': id})
    if not orden:
        return redirect('ordenes:orden_listar')

    if usuario['rol'] != 'admin' and orden['usuario']['_id'] != usuario['_id']:
        return redirect('ordenes:orden_listar')

    return mostrar_detalle(request, usuario, orden, None)


def orden_cambiar_estado(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if usuario['rol'] != 'admin':
        return redirect('ordenes:carrito_ver')

    orden = db.ordenes.find_one({'id': id})
    if not orden:
        return redirect('ordenes:orden_listar')

    if request.method != 'POST':
        return redirect('ordenes:orden_detalle', id=id)

    estado = request.POST.get('estado', '')

    if not estado_valido(estado):
        return mostrar_detalle(request, usuario, orden, 'El estado no es valido.')

    if orden['estado'] == 'cancelado':
        return mostrar_detalle(request, usuario, orden, 'Una orden cancelada no se puede modificar.')

    if estado == 'cancelado' and not se_puede_cancelar(orden):
        return mostrar_detalle(request, usuario, orden, 'Solo se pueden cancelar ordenes pendientes o pagadas.')

    db.ordenes.update_one({'_id': orden['_id']}, {'$set': {'estado': estado}})
    if estado == 'cancelado':
        devolver_stock(orden)

    return redirect('ordenes:orden_detalle', id=id)


def orden_cancelar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    orden = db.ordenes.find_one({'id': id})
    if not orden:
        return redirect('ordenes:orden_listar')

    if usuario['rol'] != 'admin' and orden['usuario']['_id'] != usuario['_id']:
        return redirect('ordenes:orden_listar')

    if not se_puede_cancelar(orden):
        return mostrar_detalle(request, usuario, orden, 'Solo se pueden cancelar ordenes pendientes o pagadas.')

    if request.method == 'POST':
        db.ordenes.update_one({'_id': orden['_id']}, {'$set': {'estado': 'cancelado'}})
        devolver_stock(orden)
        return redirect('ordenes:orden_detalle', id=id)

    return render(request, 'ordenes/orden_cancelar.html', {'orden': orden})
