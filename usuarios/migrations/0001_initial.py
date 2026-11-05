from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import djongo.models.fields
import usuarios.models
from MarketHub.conexion import db


def crear_esquema(apps, schema_editor):
    esquema = {
        'bsonType': 'object',
        'required': ['id', 'email', 'password', 'nombre', 'rol', 'activo'],
        'properties': {
            '_id': {
                'bsonType': 'objectId'
            },
            'id': {
                'bsonType': 'int'
            },
            'email': {
                'bsonType': 'string',
                'pattern': '@'
            },
            'password': {
                'bsonType': 'string'
            },
            'nombre': {
                'bsonType': 'string'
            },
            'rol': {
                'enum': ['cliente', 'admin']
            },
            'activo': {
                'bsonType': 'bool'
            },
            'direccion': {
                'bsonType': ['object', 'null'],
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
    db.command('collMod', 'usuarios', validator={'$jsonSchema': esquema})


def crear_datos(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')

    usuarios = [
        ['admin@markethub.com', 'admin123', 'Administrador', 'admin', 'Calle 1 # 2-3', 'Bogota'],
        ['ana@correo.com', 'cliente123', 'Ana Torres', 'cliente', 'Carrera 7 # 45-10', 'Bogota'],
        ['luis@correo.com', 'cliente123', 'Luis Ramirez', 'cliente', 'Calle 50 # 20-15', 'Medellin'],
        ['sofia@correo.com', 'cliente123', 'Sofia Gomez', 'cliente', 'Avenida 6 # 12-30', 'Cali'],
    ]

    for datos in usuarios:
        Usuario.objects.create(
            email=datos[0],
            password=make_password(datos[1]),
            nombre=datos[2],
            rol=datos[3],
            activo=True,
            direccion={'calle': datos[4], 'ciudad': datos[5]},
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('nombre', models.CharField(max_length=255)),
                ('rol', models.CharField(choices=[('cliente', 'Cliente'), ('admin', 'Admin')], max_length=10)),
                ('activo', models.BooleanField(default=True)),
                ('direccion', djongo.models.fields.EmbeddedField(blank=True, model_container=usuarios.models.Direccion, null=True)),
            ],
            options={
                'db_table': 'usuarios',
            },
        ),
        migrations.RunPython(crear_esquema),
        migrations.RunPython(crear_datos),
    ]
