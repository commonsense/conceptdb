import mongoengine as mon
from datetime import datetime

class Log(mon.Document):
    object = mon.GenericReferenceField(required=True)
    action = mon.StringField()
    data = mon.DictField()
    timestamp = mon.DateTimeField(default=datetime.utcnow)
    
    @staticmethod
    def add_entry(object, action, data):
        return Log.create(object=object, action=action, data=data)
    
    @staticmethod
    def record(object, is_new=False):
        if is_new: action = u'update'
        else: action = u'create'
        return Log.add_entry(object, action, {'value': object.serialize()})
    
    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
