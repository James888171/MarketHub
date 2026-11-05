from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.shortcuts import render, redirect
from productos.models import Producto
from usuarios.views import usuario_actual
from .forms import FormularioDireccion
from .models import CarritoCompras, Orden


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
    return orden.estado == 'pendiente' or orden.estado == 'pagado'


def es_dueno(usuario, orden):
    return usuario.rol == 'admin' or orden.usuario['usuario_id'] == usuario.id


def buscar_producto(producto_id):
    try:
        return Producto.objects.get(id=producto_id)
    except ObjectDoesNotExist:
        return None


def buscar_orden(id):
    try:
        return Orden.objects.get(id=id)
    except ObjectDoesNotExist:
        return None


def obtener_carrito(usuario):
    carrito = CarritoCompras.objects.filter(usuario={'usuario_id': usuario.id}).first()
    if not carrito:
        carrito = CarritoCompras.objects.create(
            usuario={
                'usuario_id': usuario.id,
                'email': usuario.email,
                'nombre': usuario.nombre,
            },
            items=[],
        )
    return carrito


def guardar_items(carrito, items):
    carrito.items = items
    carrito.save()


def devolver_stock(orden):
    for item in orden.items:
        producto = buscar_producto(item['producto']['producto_id'])
        if producto:
            producto.stock = producto.stock + item['cantidad']
            producto.save()


def calcular_total(carrito):
    total = 0
    for item in carrito.items:
        item['subtotal'] = item['producto']['precio'] * item['cantidad']
        total = total + item['subtotal']
    return total


def mostrar_carrito(request, usuario, error):
    carrito = obtener_carrito(usuario)

    contexto = {
        'carrito': carrito,
        'total': calcular_total(carrito),
        'error': error,
    }
    return render(request, 'ordenes/carrito.html', contexto)


def mostrar_confirmar(request, usuario, error, direccion):
    carrito = obtener_carrito(usuario)

    contexto = {
        'carrito': carrito,
        'total': calcular_total(carrito),
        'formulario': FormularioDireccion(initial=direccion),
        'error': error,
    }
    return render(request, 'ordenes/carrito_confirmar.html', contexto)


def mostrar_detalle(request, usuario, orden, error):
    orden.estado_nombre = nombre_estado(orden.estado)
    for item in orden.items:
        item['subtotal'] = item['precio_unitario'] * item['cantidad']

    contexto = {
        'es_admin': usuario.rol == 'admin',
        'orden': orden,
        'puede_cancelar': se_puede_cancelar(orden),
        'error': error,
    }
    return render(request, 'ordenes/orden_detalle.html', contexto)


def mostrar_estado(request, orden, error):
    orden.estado_nombre = nombre_estado(orden.estado)

    contexto = {
        'orden': orden,
        'estados': Orden.ESTADOS,
        'error': error,
    }
    return render(request, 'ordenes/orden_estado.html', contexto)


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
        producto = buscar_producto(int(producto_id))

    if not producto or not producto.activo:
        return mostrar_carrito(request, usuario, 'Debes seleccionar un producto.')

    if not cantidad.isdigit() or int(cantidad) == 0:
        return mostrar_carrito(request, usuario, 'La cantidad debe ser un número mayor a 0.')

    cantidad = int(cantidad)
    carrito = obtener_carrito(usuario)
    items = carrito.items

    encontrado = False
    for item in items:
        if item['producto']['producto_id'] == producto.id:
            item['cantidad'] = item['cantidad'] + cantidad
            cantidad = item['cantidad']
            encontrado = True

    if cantidad > producto.stock:
        return mostrar_carrito(request, usuario, 'Solo hay ' + str(producto.stock) + ' unidades de ' + producto.nombre + '.')

    if not encontrado:
        items.append({
            'producto': {
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
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

    for item in carrito.items:
        cantidad = request.POST.get('cantidad_' + str(posicion), '').strip()
        posicion = posicion + 1

        if not cantidad.isdigit():
            return mostrar_carrito(request, usuario, 'Las cantidades deben ser numeros enteros.')

        cantidad = int(cantidad)
        if cantidad == 0:
            continue

        producto = buscar_producto(item['producto']['producto_id'])
        if producto and cantidad > producto.stock:
            return mostrar_carrito(request, usuario, 'Solo hay ' + str(producto.stock) + ' unidades de ' + producto.nombre + '.')

        item['cantidad'] = cantidad
        items.append(item)

    guardar_items(carrito, items)
    return redirect('ordenes:carrito_ver')


def carrito_quitar(request, posicion):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    carrito = obtener_carrito(usuario)
    items = carrito.items
    if posicion < len(items):
        items.pop(posicion)
        guardar_items(carrito, items)

    return redirect('ordenes:carrito_ver')


def carrito_confirmar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    direccion = {}
    if usuario.direccion:
        direccion = usuario.direccion

    return mostrar_confirmar(request, usuario, None, direccion)


def carrito_finalizar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if request.method != 'POST':
        return redirect('ordenes:carrito_ver')

    carrito = obtener_carrito(usuario)
    calle = request.POST.get('calle', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()
    direccion = {'calle': calle, 'ciudad': ciudad}

    if not carrito.items:
        return mostrar_confirmar(request, usuario, 'El carrito esta vacio.', direccion)

    if not calle or not ciudad:
        return mostrar_confirmar(request, usuario, 'La direccion de envio esta incompleta.', direccion)

    items = []
    productos = []
    total = 0
    for item in carrito.items:
        producto = buscar_producto(item['producto']['producto_id'])

        if not producto or not producto.activo:
            return mostrar_confirmar(request, usuario, 'El producto ' + item['producto']['nombre'] + ' ya no esta disponible.', direccion)

        if item['cantidad'] > producto.stock:
            return mostrar_confirmar(request, usuario, 'Solo hay ' + str(producto.stock) + ' unidades de ' + producto.nombre + '.', direccion)

        items.append({
            'producto': {
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
            },
            'precio_unitario': producto.precio,
            'cantidad': item['cantidad'],
        })
        productos.append(producto)
        total = total + producto.precio * item['cantidad']

    try:
        orden = Orden.objects.create(
            usuario=carrito.usuario,
            estado='pendiente',
            items=items,
            total=total,
            direccion_envio=direccion,
        )
    except DatabaseError:
        return mostrar_confirmar(request, usuario, 'Los datos no cumplen con la validacion de la base de datos.', direccion)

    posicion = 0
    for producto in productos:
        producto.stock = producto.stock - items[posicion]['cantidad']
        producto.save()
        posicion = posicion + 1

    guardar_items(carrito, [])
    return redirect('ordenes:orden_detalle', id=orden.id)


def orden_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    es_admin = usuario.rol == 'admin'
    busqueda = request.GET.get('q', '').strip().lower()
    estado = request.GET.get('estado', '')

    ordenes = Orden.objects.all()
    if not es_admin:
        ordenes = ordenes.filter(usuario={'usuario_id': usuario.id})
    if busqueda and es_admin:
        ordenes = ordenes.filter(usuario={'email': busqueda})
    if estado:
        ordenes = ordenes.filter(estado=estado)
    ordenes = ordenes.order_by('-fecha')

    lista = []
    for orden in ordenes:
        orden.estado_nombre = nombre_estado(orden.estado)
        orden.cantidad_productos = 0
        for item in orden.items:
            orden.cantidad_productos = orden.cantidad_productos + item['cantidad']
        lista.append(orden)

    contexto = {
        'es_admin': es_admin,
        'ordenes': lista,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Orden.ESTADOS,
    }
    return render(request, 'ordenes/orden_lista.html', contexto)


def orden_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    orden = buscar_orden(id)
    if not orden or not es_dueno(usuario, orden):
        return redirect('ordenes:orden_listar')

    return mostrar_detalle(request, usuario, orden, None)


def orden_cambiar_estado(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    if usuario.rol != 'admin':
        return redirect('ordenes:carrito_ver')

    orden = buscar_orden(id)
    if not orden:
        return redirect('ordenes:orden_listar')

    if orden.estado == 'cancelado':
        return mostrar_detalle(request, usuario, orden, 'Una orden cancelada no se puede modificar.')

    if request.method != 'POST':
        return mostrar_estado(request, orden, None)

    estado = request.POST.get('estado', '')

    if not estado_valido(estado):
        return mostrar_estado(request, orden, 'El estado no es valido.')

    if estado == 'cancelado' and not se_puede_cancelar(orden):
        return mostrar_estado(request, orden, 'Solo se pueden cancelar ordenes pendientes o pagadas.')

    orden.estado = estado
    try:
        orden.save()
    except DatabaseError:
        return mostrar_estado(request, orden, 'Los datos no cumplen con la validacion de la base de datos.')

    if estado == 'cancelado':
        devolver_stock(orden)

    return redirect('ordenes:orden_detalle', id=id)


def orden_cancelar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')

    orden = buscar_orden(id)
    if not orden or not es_dueno(usuario, orden):
        return redirect('ordenes:orden_listar')

    if not se_puede_cancelar(orden):
        return mostrar_detalle(request, usuario, orden, 'Solo se pueden cancelar ordenes pendientes o pagadas.')

    if request.method == 'POST':
        orden.estado = 'cancelado'
        orden.save()
        devolver_stock(orden)
        return redirect('ordenes:orden_detalle', id=id)

    return render(request, 'ordenes/orden_cancelar.html', {'orden': orden})
