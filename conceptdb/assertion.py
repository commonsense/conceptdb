import mongoengine as mon
from mongoengine.queryset import DoesNotExist
from conceptdb.justify import Justification, ConceptDBJustified
from conceptdb.metadata import Dataset
from conceptdb.util import outer_iter
from conceptdb import ConceptDBDocument

BLANK = '*'
class Assertion(ConceptDBJustified, mon.Document):
    dataset = mon.StringField(required=True) # reference to Dataset
    relation = mon.StringField(required=True) # concept ID
    arguments = mon.ListField(mon.StringField()) # list(concept ID)
    argstr = mon.StringField()
    complete = mon.IntField() # boolean
    context = mon.StringField() # concept ID
    polarity = mon.IntField() # 1, 0, or -1
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
        return '/assertion/%s' % self.id

    @staticmethod
    def make(dataset, relation, arguments, polarity=1, context=None,
             reasons=None):
        needs_save = False
        if isinstance(arguments, basestring):
            argstr = arguments
        else:
            argstr = Assertion.make_arg_string(arguments)
        if isinstance(dataset, Dataset): dataset = dataset.name
        try:
            a = Assertion.objects.get(
                dataset=dataset,
                relation=relation,
                polarity=polarity,
                argstr=argstr,
                context=context,
            )
        except DoesNotExist:
            a = Assertion(
                dataset=dataset,
                relation=relation,
                arguments=arguments,
                argstr=argstr,
                complete=(BLANK not in arguments),
                context=context,
                polarity=polarity,
                justification=Justification.empty()
            )
            needs_save = True
        if reasons is not None:
            a.add_support(reasons)
            needs_save = True
        if needs_save: a.save()
        return a

    def make_generalizations(self, reason):
        pattern_pieces = []
        for arg in self.arguments:
            if arg == BLANK:
                pattern_pieces.append((False,))
            else:
                pattern_pieces.append((True, False))
        for pattern in outer_iter(pattern_pieces):
            if True in pattern:
                gen = self.generalize(pattern, reason)
                #gen.update_confidence()
                gen.save()
    
    def generalize(self, pattern, reason):
        args = []
        for arg, drop in zip(self.arguments, pattern):
            if drop: args.append(BLANK)
            else: args.append(arg)
        reasons = [
          (reason, 1.0),
          (self, 1.0)
        ]
        newassertion = Assertion.make(self.dataset, self.relation,
                                      args, self.polarity,
                                      self.context, reasons)
        for expr in self.get_expressions():
            newexpr = expr.generalize(pattern, newassertion, reason)
            newexpr.save()
        return newassertion

    def connect_to_sentence(self, dataset, text, reasons=None):
        sent = Sentence.make(dataset, text, reasons)
        sent.add_assertion(self)

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)
    
    def get_expressions(self):
        return Expression.objects(assertion=self)

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
    
    def make_expression(self, frame, arguments, language):
        expr = Expression.make(self, frame, arguments, language)
        for e in self.get_expressions():
            if expr == e: return e
        expr.save()
        return expr

    def __unicode__(self):
        polstr = '?'
        if self.polarity == 1: polstr = '+'
        elif self.polarity == -1: polstr = '-'
        if self.context is None: context='*'
        else: context = self.context
        rel = self.relation.split('/')[-1]
        args = ', '.join([arg.split('/')[-1] for arg in self.argstr.split(',')])
        return u"%s%s(%s) in %s:%s" % (polstr, rel, args,
                                       self.dataset, context)

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
    def make(dataset, text, reasons=None):
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
        if needs_save:
            #s.update_confidence()
            s.save()
        return s
    
    def check_consistency(self):
        # TODO: check words match up
        self.justification.check_consistency()
        self.get_dataset().check_consistency()

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def add_assertion(self, assertion):
        self.append('derived_assertions', assertion, db_only=False)

    def quick_add_assertion(self, assertion):
        self.append('derived_assertions', assertion, db_only=True)

BLANK = '*'
class Expression(ConceptDBJustified, mon.Document):
    assertion = mon.ReferenceField(Assertion, unique_with=('language', 'frame', 'text'))
    #NOTE: why are these with assertions with specific langagues
    #instead of in datasets?
    text = mon.StringField(required=True)
    frame = mon.StringField(required=True)
    language = mon.StringField(required=True)
    arguments = mon.ListField(mon.StringField())
    justification = mon.EmbeddedDocumentField(Justification)

    meta = {'indexes': ['assertion',
                        'arguments',
                        ('language', 'text'),
                        ('language', 'frame', 'text')]}

    def check_consistency(self):
        assert (Expression.replace_args(self.frame, self.arguments)
                == self.text)
        assert len(self.arguments) == len(self.assertion.arguments)

    @staticmethod
    def replace_args(frame, arguments):
        text_args = []
        for index, arg in enumerate(arguments):
            if arg == BLANK: text_args.append('{%d}' % index)
            else: text_args.append(arg)
        return frame.format(*text_args)
    
    @staticmethod
    def make(assertion, frame, arguments, language):
        text = Expression.replace_args(frame, arguments)
        return Expression(
            assertion=assertion,
            text=text,
            frame=frame,
            arguments=arguments,
            language=language,
            justification=Justification.empty()
        )
    
    @property
    def name(self):
        return "/expression/%s" % self.id

    def generalize(self, pattern, assertion, reason):
        args = []
        for arg, drop in zip(self.arguments, pattern):
            if drop: args.append(BLANK)
            else: args.append(arg)
        e = assertion.make_expression(self.frame, args, self.language)
        reasons = [
            (reason, 1.0),
            (self, 1.0)
        ]
        e.add_support(reasons)
        e.update_confidence()
        return e
        
    def add_support(self, reasons):
        self.justification = self.justification.add_support(reasons)

    def add_oppose(self, reasons):
        self.justification = self.justification.add_oppose(reasons)

    def update_confidence(self):
        self.justification.update_confidence()
    
    def __cmp__(self, other):
        if not isinstance(other, Expression): return -1
        return cmp((self.assertion, self.frame, self.text, self.language), (other.assertion, other.frame, other.text, other.language))
    
    def __eq__(self, other):
        return cmp(self, other) == 0

    def __ne__(self, other):
        return cmp(self, other) != 0

    def __hash__(self):
        return hash((self.frame, self.text))

    def __unicode__(self):
        return self.text
