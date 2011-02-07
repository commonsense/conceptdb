import mongoengine as mon
from datetime import datetime

class Log(mon.Document):
    object = mon.GenericReferenceField()
    action = mon.StringField()
    data = mon.DictField()
    timestamp = mon.DateTimeField(default=datetime.utcnow)
    
    meta = {'indexes': [('object', 'timestamp')]}
    
    @staticmethod
    def add_entry(object, action, data):
        return Log.create(object=object, action=action, data=data)
    
    @staticmethod
    def record_new(object):
        return Log.add_entry(object, 'create', {})

    @staticmethod
    def record_update(object):
        return Log.add_entry(object, 'update', {})
    
    @staticmethod
    def record_error(object, errtype, value):
        return Log.add_entry(object, 'error', {'type': errtype,
                                               'value': value})
    
    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
