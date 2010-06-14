__import__('os').environ.setdefault('DJANGO_SETTINGS_MODULE', 'csc.django_settings')
import csc.lib
import mongoengine as mon
import db_config

mon.connect('conceptdb',
            host=db_config.MONGODB_HOST,
            username=db_config.MONGODB_USER,
            password=db_config.MONGODB_PASSWORD)

class ConceptDBDocument(object):
    @classmethod
    def get(self, key):
        return cls.objects.with_id(key)

    @classmethod
    def create(cls, **fields):
        object = cls(**fields)
        object.save()
        return object

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

