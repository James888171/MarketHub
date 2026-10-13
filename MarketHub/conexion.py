from django.conf import settings
from pymongo import MongoClient

cliente = MongoClient(settings.DATABASES['default']['HOST'])
db = cliente[settings.DATABASES['default']['NAME']]


def siguiente_id(coleccion):
    ultimo = coleccion.find_one(sort=[('id', -1)])
    if ultimo:
        return ultimo['id'] + 1
    return 1
