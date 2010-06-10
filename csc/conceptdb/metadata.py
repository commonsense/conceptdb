from csc.nl import get_nl
import mongokit as mon
from csc.conceptdb import ConceptDBDocument, register

@register
class Dataset(ConceptDBDocument):
    structure = {
        'name': unicode, # primary key?
        'language': unicode,
    }
    required_fields = ['name']
    
    @property
    def nl():
        if self.language is None:
            raise ValueError("This Dataset is not associated with a natural language")
        return get_nl(self.language)

@register
class Relation(ConceptDBDocument):
    structure = {
        'name': unicode,
        'arity': int,
        'transitive': bool,
        'symmetric': bool,
    }
    required_fields = ['name']
