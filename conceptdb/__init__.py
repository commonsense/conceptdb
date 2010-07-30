__import__('os').environ.setdefault('DJANGO_SETTINGS_MODULE', 'csc.django_settings')
from conceptdb.log import Log
import mongoengine as mon
from mongoengine.queryset import DoesNotExist, QuerySet
from pymongo.objectid import ObjectId
import db_config
import json

def connect_to_mongodb(dbname='conceptdb',
                       host=db_config.MONGODB_HOST,
                       username=db_config.MONGODB_USER,
                       password=db_config.MONGODB_PASSWORD):
    """
    Connect to the given MongoDB database. By default, it will connect to
    'conceptdb' with the settings given in db_config.py, but any of these
    settings can be overridden.

    For example, to use an expendable test database, use dbname='test'
    instead.

    The majority of the methods in csc.conceptdb will not work until
    after you have used connect_to_mongodb successfully.
    """
    _db = mon.connect(dbname, host=host, username=username, password=password)
    return _db

class JSONScrubber(json.JSONEncoder):
    def _iterencode_dict(self, dct, markers=None):
        d2 = {}
        for key in dct:
            if not key.startswith('_') or key == '_id':
                d2[key] = dct[key]
        return json.JSONEncoder._iterencode_dict(self, d2, markers)
    
    def _iterencode_default(self, obj, markers):
        if isinstance(obj, ObjectId):
            yield obj.binary.encode('hex')
            return
        elif isinstance(obj, QuerySet):
            for token in self._iterencode_list(obj):
                yield token
        elif isinstance(obj, mon.Document):
            for token in self._iterencode_dict(obj.to_mongo(), markers):
                yield token
        else:
            for token in json.JSONEncoder._iterencode_default(self, obj, markers):
                yield token
        
def to_json(obj):
    return json.dumps(obj, cls=JSONScrubber)

class ConceptDBDocument(object):
    """
    A base class that provides some common functionality beyond what the
    mongoengine.Document class provides.

    It would be much better Python style if this class inherited from
    mongoengine.Document, but a bug in mongoengine prevents it from having
    multiple levels of subclasses! Our workaround for now is that every
    class of document should inherit from (ConceptDBDocument, mon.Document).
    """
    @classmethod
    def get(cls, key):
        result = cls.objects.with_id(key)
        if result is None: raise DoesNotExist
        return result

    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
        return object

    def update(self, db_only=True, **fields):
        if db_only and self.id:
            query = self.__class__.objects(id=self.id)
            update = {}
            for key, value in fields.items():
                update['set__'+key] = value
            result = query.update_one(**update)
            Log.record_update(self, fields)
            return result
        else:
            self[fieldname].append(value)

    def append(self, fieldname, value, db_only=True):
        if db_only and self.id:
            self.save()
            query = self.__class__.objects(id=self.id)
            update = {
                'push__'+fieldname: value
            }
            result = query.update_one(**update)
            Log.record_append(self, {fieldname: value})
            return result
        else:
            self[fieldname].append(value)
    
    def save(self):
        self.check_consistency()
        prevstate = None
        if getattr(self, '_id', None) is not None:
            prevstate = self.__class__.objects.with_id(self._id)
        
        result = mon.Document.save(self)
        if prevstate is None:
            Log.record_new(self)
        else:
            Log.record_diff(self, prevstate)
        return result
    
    def serialize(self):
        return self.to_mongo()
    
    def to_json(self):
        return to_json(self)

    def __repr__(self):
        assignments = ['%s=%r' % (key, value) for key, value in self.serialize().items()]
        assignments.sort()
        return "%s(%s)" % (self.__class__.__name__,
                           ', '.join(assignments))

    def __str__(self):
        return repr(self)

