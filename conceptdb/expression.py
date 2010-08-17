import mongoengine as mon
import pymongo
from conceptdb.justify import Justification, ConceptDBJustified

BLANK = '*'
class Expression(mon.EmbeddedDocument, ConceptDBJustified):
    text = mon.StringField(required=True)
    frame = mon.StringField(required=True)
    language = mon.StringField(required=True)
    arguments = mon.ListField(mon.StringField())
    name = mon.StringField()
    justification = mon.EmbeddedDocumentField(Justification)

    def check_consistency(self):
        assert (Expression.replace_args(self.frame, self.arguments)
                == self.text)
        self.justification.check_consistency()

    def generate_name(self, assertion):
        if self.name:
            raise ValueError("This expression is already named %s" % self.name)
        else:
            textid = self.text.replace(' ', '_').replace('/', '_')
            self.name = "/expression/%s/%s" % (assertion.id, textid)

    @staticmethod
    def replace_args(frame, arguments):
        text_args = []
        for index, arg in enumerate(arguments):
            if arg == BLANK: text_args.append('{%d}' % index)
            else: text_args.append(arg)
        return frame.format(*text_args)
    
    @staticmethod
    def make(frame, arguments, language):
        # I used to have "context=None" as a default here.
        # I don't remember what it was supposed to be for.
        text = Expression.replace_args(frame, arguments)
        return Expression(
            text=text,
            frame=frame,
            arguments=arguments,
            language=language,
            justification=Justification.empty()
        )

    def generalize(self, pattern, reason):
        args = []
        for arg, drop in zip(self.arguments, pattern):
            if drop: args.append(BLANK)
            else: args.append(arg)
        e = Expression.make(self.frame, args, self.language)
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
        return cmp((self.frame, self.text), (other.frame, other.text))
    
    def __eq__(self, other):
        return cmp(self, other) == 0

    def __ne__(self, other):
        return cmp(self, other) != 0

    def __hash__(self):
        return hash((self.frame, self.text))

    def __unicode__(self):
        return self.text
