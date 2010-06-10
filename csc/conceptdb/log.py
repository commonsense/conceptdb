import mongokit as mon
from datetime import datetime
from csc.conceptdb import ConceptDBDocument, register

@register
class Log(ConceptDBDocument):
    structure = {
        'object': None,
        'action': unicode,
        'data': dict,
        'timestamp': datetime
    }
    defaults = {
        'timestamp': datetime.utcnow
    }

    @staticmethod
    def add_entry(object, action, data):
        Log.create(object=object, action=action, data=data)
    
    @staticmethod
    def record(object, is_new=False):
        if is_new: action = u'update'
        else: action = u'create'
        Log.add_entry(object, action, {'value': object})
