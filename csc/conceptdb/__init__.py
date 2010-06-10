__import__('os').environ.setdefault('DJANGO_SETTINGS_MODULE', 'csc.django_settings')
import csc.lib
import mongokit as mon
from django.conf.settings import mongo_connection

def register(cls):
    mongo_connection.register([cls])
    return cls

class ConceptDBDocument(mon.Document):
    def __init__(self, **fields):
        mon.Document.__init__(self)
        for key, value in fields.items():
            self[key] = value
    
    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()

