__import__('os').environ.setdefault('DJANGO_SETTINGS_MODULE', 'csc.django_settings')
import csc.lib
import mongoengine as mon
import db_config

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
    mon.connect(dbname, host=host, username=username, password=password)

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
    def get(self, key):
        return cls.objects.with_id(key)

    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
        return object

    def update(self, **fields):
        query = self.__class__.objects(id=self.id)
        update = {}
        for key, value in fields.items():
            update['set__'+key] = value
        return query.update_one(**update)

    def append(self, fieldname, value):
        query = self.__class__.objects(id=self.id)
        update = {
            'push__'+fieldname: value
        }
        return query.update_one(**update)


    def serialize(self):
        d = {}
        for field in self._fields:
            value = getattr(self, field)
            if isinstance(value, ConceptDBDocument):
                value = value.serialize()
            d[field] = value
        return d

    def __repr__(self):
        assignments = ['%s=%r' % (key, value) for key, value in self.serialize().items()]
        assignments.sort()
        return "%s(%s)" % (self.__class__.__name__,
                           ', '.join(assignments))

    def __str__(self):
        return repr(self)

