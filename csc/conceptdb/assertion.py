import mongoengine as mon
from mongoengine.queryset import DoesNotExist
from csc.conceptdb.justify import Justification, ConceptDBJustified
from csc.conceptdb.expression import Expression
from csc.conceptdb.metadata import Dataset
from csc.conceptdb import ConceptDBDocument

class Assertion(ConceptDBJustified, mon.Document):
    dataset = mon.StringField(required=True) # reference to Dataset
    relation = mon.StringField(required=True) # concept ID
    arguments = mon.ListField(mon.StringField()) # list(concept ID)
    argstr = mon.StringField()
    complete = mon.IntField() # boolean
    context = mon.StringField() # concept ID
    polarity = mon.IntField() # 1, 0, or -1
    expressions = mon.ListField(mon.EmbeddedDocumentField(Expression))
    justification = mon.EmbeddedDocumentField(Justification)

    meta = {'indexes': ['arguments',
                        ('arguments', '-justification.confidence_score'),
                        ('dataset', 'relation', 'polarity', 'argstr', 'context'),
                        'justification.support_flat',
                        'justification.oppose_flat',
                        'justification.confidence_score',
                       ]}
    
    @staticmethod
    def make_arg_string(arguments):
        def sanitize(arg):
            return arg.replace(',','_')
        return ','.join(sanitize(arg) for arg in arguments)

    @property
    def name(self):
        return '/assertion/%s' % self._id

    @staticmethod
    def make(dataset, relation, arguments, polarity=1, context=None,
             reasons=None):
        needs_save = False
        try:
            a = Assertion.objects.get(
                dataset=dataset,
                relation=relation,
                polarity=polarity,
                argstr=Assertion.make_arg_string(arguments),
                context=context
            )
        except DoesNotExist:
            a = Assertion(
                dataset=dataset,
                relation=relation,
                arguments=arguments,
                argstr=Assertion.make_arg_string(arguments),
                complete=('*' not in arguments),
                context=context,
                polarity=polarity,
                expressions=[],
                justification=Justification.empty()
            )
            needs_save = True
        if reasons is not None:
            a.add_support(reasons)
            needs_save = True
        if needs_save: a.save()
        return a

    def connect_to_sentence(self, dataset, text):
        sent = Sentence.make(dataset, text)
        sent.add_assertion(self)

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def check_consistency(self):
        # TODO: more consistency checks
        assert (self.polarity == 1 or self.polarity == 0 or self.polarity == -1) #valid polarity
        assert (self.complete == 1 or self.complete == 0) #valid boolean value

        #maybe there should be checks with relation to # of arguments
        #how will more than 2 concepts as arguments work? 1 specific
        #example was VSO, where 3 concepts would map to a relation
        #I would put in a check which makes sure that there are the
        #correct number of concepts for a given relation.

        self.justification.check_consistency()
    
    def add_expression(self, expr):
        self.append('expressions', expr)

class Sentence(ConceptDBJustified, mon.Document):
    text = mon.StringField(required=True)
    words = mon.ListField(mon.StringField())
    dataset = mon.StringField(required=True)
    justification = mon.EmbeddedDocumentField(Justification)
    derived_assertions = mon.ListField(mon.ReferenceField(Assertion))

    meta = {'indexes': ['dataset', 'words', 'text',
                        'justification.support_flat',
                        'justification.oppose_flat',
                        'justification.confidence_score',
                       ]}
    
    @staticmethod
    def make(dataset, text, reasons=[]):
        needs_save = False
        if isinstance(dataset, basestring):
            datasetObj = Dataset.get(dataset)
        else:
            datasetObj = dataset
            dataset = datasetObj.name
        try:
            s = Sentence.objects.get(dataset=dataset, text=text)
        except DoesNotExist:
            s = Sentence(
                text=text,
                dataset=dataset,
                words=datasetObj.nl.normalize(text).split(),
                justification=Justification.empty(),
                derived_assertions=[]
               )
            needs_save = True
        if reasons is not None:
            s.add_support(reasons)
            needs_save = True
        if needs_save: s.save()
        return s
    
    def check_consistency(self):
        # TODO: check words match up
        self.justification.check_consistency()
        self.get_dataset().check_consistency()

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def add_assertion(self, assertion):
        self.append('derived_assertions', assertion)

