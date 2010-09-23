from csc.nl import get_nl
from conceptdb import ConceptDBDocument
from conceptdb.justify import ConceptDBJustified
from mongoengine.queryset import DoesNotExist
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
    def make(name, language):
        #why is the language a dictionary now? - EH 7/23
        d = Dataset.objects.get_or_create(name=name,
              defaults=dict(language=language))
        return d

    def check_consistency(self):
        assert self.name.startswith('/data/')

    def get_reason(self, reason_name):
        return self.name+reason_name

    def get_root_reason(self):
        return self.get_reason('/root')


