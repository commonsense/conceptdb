from csc.nl import get_nl
from csc.conceptdb import ConceptDBDocument
import mongoengine as mon

class Dataset(ConceptDBDocument, mon.Document):
    name = mon.StringField(primary_key=True)
    language = mon.StringField()
    
    @property
    def nl(self):
        if self.language is None:
            raise ValueError("This Dataset is not associated with a natural language")
        return get_nl(self.language)
    
    @staticmethod
    def get(name):
        return Dataset.objects.with_id(name)
    
    @staticmethod
    def make(name, language):
        d = Dataset.objects.get_or_create(name=name,
              defaults=dict(language=language))
        return d
    
