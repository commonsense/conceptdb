import mongoengine as mon
from datetime import datetime

class Log(mon.Document):
    object = mon.GenericReferenceField(required=True)
    action = mon.StringField()
    data = mon.DictField()
    timestamp = mon.DateTimeField(default=datetime.utcnow)
    
    meta = {'indexes': [('object', 'timestamp')]}
    
    @staticmethod
    def add_entry(object, action, data):
        return Log.create(object=object, action=action, data=data)
    
    @staticmethod
    def record_new(object):
        return Log.add_entry(object, 'create', {'value': object.serialize()})

    @staticmethod
    def record_diff(object, saved):
        changed = {}
        for field in object._fields:
            newval = getattr(obj, field)
            oldval = getattr(saved, field, None)
            if newval != oldval:
                changed[field] = newval
        return Log.record_update(object, changed)

    @staticmethod
    def record_update(object, changed):
        for key, value in changed.items():
            if isinstance(value, (mon.Document, mon.EmbeddedDocument)):
                changed[key] = object.to_mongo()
        return Log.add_entry(object, 'update', {'value': changed})
    
    @staticmethod
    def record_append(object, changed):
        for key, value in changed.items():
            if isinstance(value, (mon.Document, mon.EmbeddedDocument)):
                changed[key] = object.to_mongo()
        return Log.add_entry(object, 'append', {'value': changed})
    
    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
