from csc.nl import get_nl
from conceptdb import ConceptDBDocument
from conceptdb.justify import Justification, ConceptDBJustified
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
        if isinstance(reason_name, ConceptDBDocument):
            assert reason_name.dataset == self.name
            return reason_name
        else:
            assert isinstance(reason_name, basestring)
            if reason_name.startswith('/assertion/'):
                from conceptdb.assertion import Assertion
                parts = reason_name.split('/')
                a_name = parts[2]
                assertion = Assertion.objects.with_name(a_name)
                assert assertion.dataset == self.name
                return assertion
            elif reason_name.startswith('/data/'):
                assert reason_name.startswith(self.name)
                return ExternalReason.objects.with_name(reason_name)
            else:
                full_name = self.name+reason_name
                return ExternalReason.objects.with_name(full_name)
    
    def get_reason_name(self, reason_name):
        return self.name+reason_name

    def get_root_reason(self):
        return ExternalReason.make(self.name, '/root')
    
EXT_REASON_TYPES = ['root', 'admin', 'site', 'contributor', 'rule', 'activity']
class ExternalReason(mon.Document, ConceptDBJustified):
    """
    An ExternalReason is a unit of justification. It indicates a reason to
    believe some ConceptDBJustified object, when that reason is represented
    outside of ConceptDB.

    ExternalReasons must be associated with a particular dataset, so that they
    are consistent with Assertions, and so that they can be synced between
    different ConceptDBs independently.

    Assertions are not the same as Reasons, but they may also be used as
    units of justification. Use justify.lookup_reason() to get the appropriate
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
        try:
            r = ExternalReason.get(name)
        except DoesNotExist:
            r = ExternalReason(
                name=name,
                dataset=dataset,
                justification=Justification.empty(),
               )
            if name_suffix == '/root':
                r.justification.confidence_score = 1.0
            needs_save = True
        if reasons is not None:
            r.add_support(reasons)
            needs_save = True
        if needs_save:
            r.update_confidence()
            r.save()
        return r

    def update_confidence(self):
        if self.name_suffix() == '/root': return
        ConceptDBJustified.update_confidence(self)

    def check_consistency(self):
        assert self.name.startswith(self.dataset)
        assert self.name_suffix().startswith('/')
        assert self.type() in EXT_REASON_TYPES
        self.justification.check_consistency()
        self.get_dataset()
    
    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def name_suffix(self):
        return self.name[len(self.dataset):]

    def derived_reason(self, name_suffix, weight=1.0):
        return ExternalReason.make(self.dataset, name_suffix, [(self, weight)])

    def type(self):
        return self.name_suffix().split('/')[1]
    
    def __str__(self):
        return "<ExternalReason: %s>" % self.name
    def __repr__(self):
        return "<ExternalReason: %s>" % self.name
