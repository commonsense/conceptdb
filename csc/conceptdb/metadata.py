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

    def get_reason(self, reason):
        if isinstance(reason, ConceptDBDocument):
            assert reason.dataset == self.name
            return reason
        else:
            assert isinstance(reason, basestring)
            if reason.startswith('/assertion/'):
                from csc.conceptdb.assertion import Assertion
                parts = reason.split('/')
                a_id = parts[2]
                assertion = Assertion.objects.with_id(a_id)
                assert assertion.dataset == self.name
                return assertion
            elif reason.startswith('/data/'):
                assert reason.startswith(self.name)
                return ExternalReason.objects.with_id(reason)
            else:
                full_id = self.name+reason
                return ExternalReason.objects.with_id(full_id)

    def get_root_reason(self):
        return ExternalReason.make(self, '/root')
    
EXT_REASON_TYPES = ['root', 'admin', 'site', 'contributor', 'algorithm']
class ExternalReason(mon.Document, ConceptDBJustified):
    """
    An ExternalReason is a unit of justification. It indicates a reason to
    believe some ConceptDBJustified object, when that reason is represented
    outside of ConceptDB.

    ExternalReasons must be associated with a particular dataset, so that they
    are consistent with Assertions, and so that they can be synced between
    different ConceptDBs independently.

    Assertions are not the same as Reasons, but they may also be used as
    units of justification. Use justify.lookup() to get the appropriate
    Assertion or Reason from an ID.
    """
    name = mon.StringField(required=True, primary_key=True)
    justification = mon.EmbeddedDocumentField(Justification)
    dataset = mon.StringField(required=True)
    
    meta = {'indexes': ['dataset', 'name',
                        'justification.support_flat',
                        'justification.oppose_flat',
                        'justification.confidence_score',
                       ]}
    
    @staticmethod
    def make(dataset, name_suffix, reasons=None):
        needs_save = False
        if isinstance(dataset, basestring):
            datasetObj = Dataset.get(dataset)
        else:
            datasetObj = dataset
            dataset = datasetObj.name
        name = dataset + name_suffix
        try :
            r = ExternalReason.objects.with_id(name)
        except DoesNotExist:
            r = ExternalReason(
                name=name,
                dataset=dataset,
                justification=Justification.empty(),
               )
            needs_save = True
        if reasons is not None:
            r.add_support(reasons)
            needs_save = True
        if needs_save: r.save()
        return r

    def check_consistency(self):
        assert self.name.startswith(self.dataset)
        assert self.name_suffix.startswith('/')
        assert self.type() in EXT_REASON_TYPES
        self.justification.check_consistency()
    
    def name_suffix(self):
        return self.name[len(self.dataset):]

    def derived_reason(self, name_suffix):
        return ExternalReason.make(self.dataset, name_suffix, [self])

    def type(self):
        return self.name_suffix().split('/')[1]

