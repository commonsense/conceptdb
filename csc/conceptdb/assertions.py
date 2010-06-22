import mongoengine as mon
from mongoengine.queryset import DoesNotExist
from csc.conceptdb.justify import Justification, Reason
from csc.conceptdb.metadata import Dataset
from csc.conceptdb import ConceptDBDocument

class Expression(mon.EmbeddedDocument):
    text = mon.StringField(required=True)
    language = mon.StringField(required=True)
    justification = mon.EmbeddedDocumentField(Justification)

class Assertion(ConceptDBDocument, mon.Document):
    dataset = mon.StringField(required=True)     # reference to Dataset
    relation = mon.StringField(required=True)    # concept ID
    arguments = mon.ListField(mon.StringField()) # list(concept ID)
    argstr = mon.StringField()
    complete = mon.IntField()                    # boolean
    context = mon.StringField()                  # concept ID
    polarity = mon.IntField()                    # 1, 0, or -1
    expressions = mon.ListField(mon.EmbeddedDocumentField(Expression))
    justification = mon.EmbeddedDocumentField(Justification)

    meta = {'indexes': ['arguments',
                        ('arguments', '-justification.confidence_score'),
                        ('dataset', 'relation', 'polarity', 'argstr'),
                        'justification.support_flat',
                        'justification.oppose_flat',
                        'justification.confidence_score',
                       ]}
    
    @staticmethod
    def make_arg_string(arguments):
        def sanitize(arg):
            return arg.replace(',','_')
        return ','.join(sanitize(arg) for arg in arguments)

    @staticmethod
    def make(dataset, relation, arguments, polarity=1, context=None):
        try:
            a = Assertion.objects.get(
                dataset=dataset,
                relation=relation,
                arguments=arguments,
                argstr=Assertion.make_arg_string(arguments),
                polarity=polarity,
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
            a.save()
        return a

    def connect_to_sentence(self, dataset, text):
        sent = Sentence.make(dataset, text)
        sent.add_assertion(self)

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def check_consistency(self):
        # TODO: more consistency checks
	assert (polarity == 1 or polarity == 0 or polarity == -1) #valid polarity
	assert (complete == 1 or complete == 0) #valid boolean value

	#maybe there should be checks with relation to # of arguments
	#how will more than 2 concepts as arguments work?  1 specific
	#example was VSO, where 3 concepts would map to a relation
	#I would put in a check which makes sure that there are the
	#correct number of concepts for a given relation.  

        self.justification.check_consistency()

class Sentence(ConceptDBDocument, mon.Document):
    text = mon.StringField(required=True)
    words = mon.ListField(mon.StringField())
    dataset = mon.StringField(required=True)
    justification = mon.EmbeddedDocumentField(Justification)
    derived_assertions = mon.ListField(mon.ReferenceField(Assertion))

    @staticmethod
    def make(dataset, text):
        if  isinstance(dataset, basestring):
            datasetObj = Dataset.get(dataset)
        else:
	        datasetObj = dataset
            dataset = datasetObj.name
        try:
            s = Sentence.objects.get(dataset=dataset, text=text)
        except DoesNotExist:
            s = Sentence.create(
                text=text,
                dataset=dataset,
                words=datasetObj.nl.normalize(text).split(),
                justification=Justification.empty(),
                derived_assertions=[]
               )
        return s
    
    def add_assertion(self, assertion):
        self.update(derived_assertions=self.derived_assertions + [assertion])

