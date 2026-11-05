import os
import six
import django
import django.utils
from datetime import datetime

django.utils.six = six

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MarketHub.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from MarketHub.conexion import db, siguiente_id
from categorias.models import Categoria


def crear_usuario(email, password, nombre, rol, calle, ciudad):
    usuario = {
        'id': siguiente_id(db.usuarios),
        'email': email,
        'password': make_password(password),
        'nombre': nombre,
        'rol': rol,
        'activo': True,
        'direccion': {'calle': calle, 'ciudad': ciudad},
    }
    db.usuarios.insert_one(usuario)
    return usuario


def crear_categoria(nombre, descripcion):
    categoria = Categoria.objects.create(nombre=nombre, descripcion=descripcion, activo=True)
    return db.categorias.find_one({'id': categoria.id})


def crear_producto(nombre, precio, stock, categoria):
    producto = {
        'id': siguiente_id(db.productos),
        'nombre': nombre,
        'precio': precio,
        'stock': stock,
        'categoria': {
            '_id': categoria['_id'],
            'nombre': categoria['nombre'],
            'descripcion': categoria.get('descripcion'),
        },
        'activo': True,
    }
    db.productos.insert_one(producto)
    return producto


def crear_orden(usuario, productos, cantidades, estado):
    items = []
    total = 0
    for i in range(len(productos)):
        producto = productos[i]
        cantidad = cantidades[i]
        items.append({
            'producto': {
                '_id': producto['_id'],
                'nombre': producto['nombre'],
                'precio': producto['precio'],
            },
            'precio_unitario': producto['precio'],
            'cantidad': cantidad,
        })
        total = total + producto['precio'] * cantidad
        if estado != 'cancelado':
            db.productos.update_one({'_id': producto['_id']}, {'$inc': {'stock': -cantidad}})

    db.ordenes.insert_one({
        'id': siguiente_id(db.ordenes),
        'usuario': {
            '_id': usuario['_id'],
            'email': usuario['email'],
            'nombre': usuario['nombre'],
        },
        'fecha': datetime.now(),
        'estado': estado,
        'items': items,
        'total': total,
        'direccion_envio': usuario['direccion'],
    })


if db.usuarios.find_one({'email': 'admin@markethub.com'}):
    print('Los datos de prueba ya estan cargados.')
else:
    admin = crear_usuario('admin@markethub.com', 'admin123', 'Administrador', 'admin', 'Calle 1 # 2-3', 'Bogota')
    ana = crear_usuario('ana@correo.com', 'cliente123', 'Ana Torres', 'cliente', 'Carrera 7 # 45-10', 'Bogota')
    luis = crear_usuario('luis@correo.com', 'cliente123', 'Luis Ramirez', 'cliente', 'Calle 50 # 20-15', 'Medellin')
    sofia = crear_usuario('sofia@correo.com', 'cliente123', 'Sofia Gomez', 'cliente', 'Avenida 6 # 12-30', 'Cali')

    tecnologia = crear_categoria('Tecnologia', 'Computadores, celulares y accesorios')
    hogar = crear_categoria('Hogar', 'Articulos para la casa')
    ropa = crear_categoria('Ropa', 'Ropa y calzado')
    deportes = crear_categoria('Deportes', 'Implementos deportivos')

    portatil = crear_producto('Portatil Lenovo', 2500000, 10, tecnologia)
    celular = crear_producto('Celular Samsung', 1200000, 15, tecnologia)
    audifonos = crear_producto('Audifonos Bluetooth', 150000, 30, tecnologia)
    mouse = crear_producto('Mouse inalambrico', 60000, 40, tecnologia)
    licuadora = crear_producto('Licuadora', 180000, 12, hogar)
    cafetera = crear_producto('Cafetera', 220000, 8, hogar)
    sabanas = crear_producto('Juego de sabanas', 90000, 20, hogar)
    camiseta = crear_producto('Camiseta basica', 35000, 50, ropa)
    jean = crear_producto('Jean clasico', 120000, 25, ropa)
    tenis = crear_producto('Tenis deportivos', 250000, 18, ropa)
    balon = crear_producto('Balon de futbol', 80000, 22, deportes)
    pesas = crear_producto('Pesas 5 kg', 110000, 10, deportes)


    crear_orden(ana, [celular, audifonos], [1, 2], 'pendiente')
    crear_orden(ana, [camiseta, jean], [3, 1], 'entregado')
    crear_orden(luis, [portatil, mouse], [1, 1], 'pagado')
    crear_orden(luis, [balon], [2], 'enviado')
    crear_orden(sofia, [licuadora, cafetera], [1, 1], 'cancelado')
    crear_orden(sofia, [tenis, pesas], [1, 2], 'pendiente')

    db.carritocompras.insert_one({
        'id': siguiente_id(db.carritocompras),
        'usuario': {
            '_id': ana['_id'],
            'email': ana['email'],
            'nombre': ana['nombre'],
        },
        'items': [
            {'producto': {'_id': sabanas['_id'], 'nombre': sabanas['nombre'], 'precio': sabanas['precio']}, 'cantidad': 2},
            {'producto': {'_id': mouse['_id'], 'nombre': mouse['nombre'], 'precio': mouse['precio']}, 'cantidad': 1},
        ],
        'actualizado_en': datetime.now(),
    })

    print('Datos de prueba cargados.')
