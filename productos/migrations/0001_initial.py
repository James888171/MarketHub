from django.db import migrations, models
import djongo.models.fields
import productos.models
from MarketHub.conexion import db


def crear_esquema(apps, schema_editor):
    esquema = {
        'bsonType': 'object',
        'required': ['id', 'nombre', 'precio', 'stock', 'categoria', 'activo'],
        'properties': {
            '_id': {
                'bsonType': 'objectId'
            },
            'id': {
                'bsonType': 'int'
            },
            'nombre': {
                'bsonType': 'string'
            },
            'precio': {
                'bsonType': 'int'
            },
            'stock': {
                'bsonType': 'int'
            },
            'categoria': {
                'bsonType': 'object',
                'required': ['categoria_id', 'nombre'],
                'properties': {
                    'categoria_id': {'bsonType': 'int'},
                    'nombre': {'bsonType': 'string'},
                    'descripcion': {'bsonType': ['string', 'null']}
                }
            },
            'activo': {
                'bsonType': 'bool'
            }
        },
        'minProperties': 7,
        'maxProperties': 7,
        'additionalProperties': False
    }
    db.command('collMod', 'productos', validator={'$jsonSchema': esquema})


def crear_datos(apps, schema_editor):
    Categoria = apps.get_model('categorias', 'Categoria')
    Producto = apps.get_model('productos', 'Producto')

    productos = [
        ['Portatil Lenovo', 2500000, 10, 'Tecnologia'],
        ['Celular Samsung', 1200000, 15, 'Tecnologia'],
        ['Audifonos Bluetooth', 150000, 30, 'Tecnologia'],
        ['Mouse inalambrico', 60000, 40, 'Tecnologia'],
        ['Licuadora', 180000, 12, 'Hogar'],
        ['Cafetera', 220000, 8, 'Hogar'],
        ['Juego de sabanas', 90000, 20, 'Hogar'],
        ['Camiseta basica', 35000, 50, 'Ropa'],
        ['Jean clasico', 120000, 25, 'Ropa'],
        ['Tenis deportivos', 250000, 18, 'Ropa'],
        ['Balon de futbol', 80000, 22, 'Deportes'],
        ['Pesas 5 kg', 110000, 10, 'Deportes'],
    ]

    for datos in productos:
        categoria = Categoria.objects.get(nombre=datos[3])
        Producto.objects.create(
            nombre=datos[0],
            precio=datos[1],
            stock=datos[2],
            categoria={
                'categoria_id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion,
            },
            activo=True,
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categorias', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('precio', models.IntegerField()),
                ('stock', models.IntegerField()),
                ('categoria', djongo.models.fields.EmbeddedField(model_container=productos.models.CategoriaSnapshot)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'productos',
            },
        ),
        migrations.RunPython(crear_esquema),
        migrations.RunPython(crear_datos),
    ]
