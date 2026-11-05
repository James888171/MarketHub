from django.conf import settings
from pymongo import MongoClient

cliente = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
db = cliente[settings.DATABASES['default']['NAME']]
