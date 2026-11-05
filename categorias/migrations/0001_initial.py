from django.db import migrations, models
from MarketHub.conexion import db


def crear_esquema(apps, schema_editor):
    esquema = {
        'bsonType': 'object',
        'required': ['id', 'nombre', 'activo'],
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
            'descripcion': {
                'bsonType': ['string', 'null']
            },
            'activo': {
                'bsonType': 'bool'
            }
        },
        'minProperties': 4,
        'maxProperties': 5,
        'additionalProperties': False
    }
    db.command('collMod', 'categorias', validator={'$jsonSchema': esquema})


def crear_datos(apps, schema_editor):
    Categoria = apps.get_model('categorias', 'Categoria')

    categorias = [
        ['Tecnologia', 'Computadores, celulares y accesorios'],
        ['Hogar', 'Articulos para la casa'],
        ['Ropa', 'Ropa y calzado'],
        ['Deportes', 'Implementos deportivos'],
    ]

    for datos in categorias:
        Categoria.objects.create(nombre=datos[0], descripcion=datos[1], activo=True)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'categorias',
            },
        ),
        migrations.RunPython(crear_esquema),
        migrations.RunPython(crear_datos),
    ]
