import mongoengine as mon
from mongoengine.queryset import DoesNotExist
from csc.conceptdb.justify import Justification

BLANK = '*'
class Expression(mon.EmbeddedDocument):
    text = mon.StringField(required=True)
    frame = mon.StringField(required=True)
    language = mon.StringField(required=True)
    arguments = mon.ListField(mon.StringField())
    justification = mon.EmbeddedDocumentField(Justification)

    def check_consistency(self):
        assert (Expression.replace_args(self.frame, self.arguments)
                == self.text)
        self.justification.check_consistency()

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
        
    def add_support(self):
        self.justification = self.justification.add_support(self)

    def add_oppose(self):
        self.justification = self.justification.add_oppose(self)

