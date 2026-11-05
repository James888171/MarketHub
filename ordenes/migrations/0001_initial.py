from django.db import migrations, models
import djongo.models.fields
import ordenes.models
from MarketHub.conexion import db


def crear_esquema(apps, schema_editor):
    esquema_carrito = {
        'bsonType': 'object',
        'required': ['id', 'usuario', 'items'],
        'properties': {
            '_id': {
                'bsonType': 'objectId'
            },
            'id': {
                'bsonType': 'int'
            },
            'usuario': {
                'bsonType': 'object',
                'required': ['usuario_id', 'email', 'nombre'],
                'properties': {
                    'usuario_id': {'bsonType': 'int'},
                    'email': {'bsonType': 'string'},
                    'nombre': {'bsonType': 'string'}
                }
            },
            'actualizado_en': {
                'bsonType': 'date'
            },
            'items': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'object',
                    'required': ['producto', 'cantidad'],
                    'properties': {
                        'producto': {
                            'bsonType': 'object',
                            'required': ['producto_id', 'nombre', 'precio'],
                            'properties': {
                                'producto_id': {'bsonType': 'int'},
                                'nombre': {'bsonType': 'string'},
                                'precio': {'bsonType': 'int'}
                            }
                        },
                        'cantidad': {'bsonType': 'int'}
                    }
                }
            }
        },
        'minProperties': 4,
        'maxProperties': 5,
        'additionalProperties': False
    }

    esquema_orden = {
        'bsonType': 'object',
        'required': ['id', 'usuario', 'fecha', 'estado', 'items', 'total'],
        'properties': {
            '_id': {
                'bsonType': 'objectId'
            },
            'id': {
                'bsonType': 'int'
            },
            'usuario': {
                'bsonType': 'object',
                'required': ['usuario_id', 'email', 'nombre'],
                'properties': {
                    'usuario_id': {'bsonType': 'int'},
                    'email': {'bsonType': 'string'},
                    'nombre': {'bsonType': 'string'}
                }
            },
            'fecha': {
                'bsonType': 'date'
            },
            'estado': {
                'enum': ['pendiente', 'pagado', 'enviado', 'entregado', 'cancelado']
            },
            'items': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'object',
                    'required': ['producto', 'precio_unitario', 'cantidad'],
                    'properties': {
                        'producto': {
                            'bsonType': 'object',
                            'required': ['producto_id', 'nombre', 'precio'],
                            'properties': {
                                'producto_id': {'bsonType': 'int'},
                                'nombre': {'bsonType': 'string'},
                                'precio': {'bsonType': 'int'}
                            }
                        },
                        'precio_unitario': {'bsonType': 'int'},
                        'cantidad': {'bsonType': 'int'}
                    }
                }
            },
            'total': {
                'bsonType': 'int'
            },
            'direccion_envio': {
                'bsonType': 'object',
                'required': ['calle', 'ciudad'],
                'properties': {
                    'calle': {'bsonType': 'string'},
                    'ciudad': {'bsonType': 'string'}
                }
            }
        },
        'minProperties': 7,
        'maxProperties': 8,
        'additionalProperties': False
    }

    db.command('collMod', 'carritocompras', validator={'$jsonSchema': esquema_carrito})
    db.command('collMod', 'ordenes', validator={'$jsonSchema': esquema_orden})


def crear_orden(Orden, Producto, usuario, nombres, cantidades, estado):
    items = []
    total = 0
    posicion = 0
    for nombre in nombres:
        producto = Producto.objects.get(nombre=nombre)
        cantidad = cantidades[posicion]
        items.append({
            'producto': {
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
            },
            'precio_unitario': producto.precio,
            'cantidad': cantidad,
        })
        total = total + producto.precio * cantidad
        if estado != 'cancelado':
            producto.stock = producto.stock - cantidad
            producto.save()
        posicion = posicion + 1

    Orden.objects.create(
        usuario={
            'usuario_id': usuario.id,
            'email': usuario.email,
            'nombre': usuario.nombre,
        },
        estado=estado,
        items=items,
        total=total,
        direccion_envio=usuario.direccion,
    )


def crear_datos(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Producto = apps.get_model('productos', 'Producto')
    Orden = apps.get_model('ordenes', 'Orden')
    CarritoCompras = apps.get_model('ordenes', 'CarritoCompras')

    ana = Usuario.objects.get(email='ana@correo.com')
    luis = Usuario.objects.get(email='luis@correo.com')
    sofia = Usuario.objects.get(email='sofia@correo.com')

    crear_orden(Orden, Producto, ana, ['Celular Samsung', 'Audifonos Bluetooth'], [1, 2], 'pendiente')
    crear_orden(Orden, Producto, ana, ['Camiseta basica', 'Jean clasico'], [3, 1], 'entregado')
    crear_orden(Orden, Producto, luis, ['Portatil Lenovo', 'Mouse inalambrico'], [1, 1], 'pagado')
    crear_orden(Orden, Producto, luis, ['Balon de futbol'], [2], 'enviado')
    crear_orden(Orden, Producto, sofia, ['Licuadora', 'Cafetera'], [1, 1], 'cancelado')
    crear_orden(Orden, Producto, sofia, ['Tenis deportivos', 'Pesas 5 kg'], [1, 2], 'pendiente')

    sabanas = Producto.objects.get(nombre='Juego de sabanas')
    mouse = Producto.objects.get(nombre='Mouse inalambrico')

    CarritoCompras.objects.create(
        usuario={
            'usuario_id': ana.id,
            'email': ana.email,
            'nombre': ana.nombre,
        },
        items=[
            {'producto': {'producto_id': sabanas.id, 'nombre': sabanas.nombre, 'precio': sabanas.precio}, 'cantidad': 2},
            {'producto': {'producto_id': mouse.id, 'nombre': mouse.nombre, 'precio': mouse.precio}, 'cantidad': 1},
        ],
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usuarios', '0001_initial'),
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarritoCompras',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', djongo.models.fields.EmbeddedField(model_container=ordenes.models.UsuarioSnapshot)),
                ('items', djongo.models.fields.ArrayField(model_container=ordenes.models.ItemCarrito)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'carritocompras',
            },
        ),
        migrations.CreateModel(
            name='Orden',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', djongo.models.fields.EmbeddedField(model_container=ordenes.models.UsuarioSnapshot)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado'), ('enviado', 'Enviado'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('items', djongo.models.fields.ArrayField(model_container=ordenes.models.ItemOrden)),
                ('total', models.IntegerField()),
                ('direccion_envio', djongo.models.fields.EmbeddedField(model_container=ordenes.models.DireccionEnvio)),
            ],
            options={
                'db_table': 'ordenes',
            },
        ),
        migrations.RunPython(crear_esquema),
        migrations.RunPython(crear_datos),
    ]
