import mongoengine as mon
from conceptdb import ConceptDBDocument, to_json
from log import Log
import numpy as np

def ensure_reference(obj):
    if isinstance(obj, basestring): return obj
    elif isinstance(obj, ConceptDBDocument): return obj.name
    else:
        raise ValueError("Don't know how to reference %s" % obj)

class Reason(ConceptDBDocument, mon.Document):
    # target: What is this a reason for?
    # (Expressed as a URL that may or may not refer to a DB object.)
    target = mon.StringField()

    # factors: What things must be true for this reason to be true?
    # (That is, the factors form a conjunction.)
    factors = mon.ListField(mon.StringField())

    # weight: How much do we inherently believe this reason, independently
    # of how much we believe its factors?
    # (Changed from "weights" because there's no reason to keep them as
    # separate factors)
    weight = mon.FloatField()

    # polarity: Is this a reason to believe or disbelieve its target?
    polarity = mon.BooleanField()
    
    # confidence_update: Has the weight of this reason been added to the target's
    # confidence value yet?
    #confidence_update = mon.BooleanField()

    meta = {'indexes': [('target', 'polarity'),
                        'factors']}

    @staticmethod
    def make(target, factors, weight, polarity):
        target = ensure_reference(target)
        factors = [ensure_reference(f) for f in factors]
        #confidence_update=False
        r = Reason.objects.get_or_create(
            target=target,
            factors__all=factors,
            polarity=polarity,
            defaults={'factors': factors, 'weight': weight}
        )
        if r[0].id is not None:
            # FIXME: this minimizes the number of factors at all costs.
            # Occam's supercharged electric razor may not be exactly the right
            # criterion.
            r[0].factors = factors
            r[0].weight = weight
            #r[0].confidence_update=confidence_update
        return r[0]

    def check_consistency(self):
        assert 0.0 <= self.weight <= 1.0

def justify(target, factors, weight):
    return Reason.make(target, factors, weight, True)

class ConceptDBJustified(ConceptDBDocument):
    """
    Documents that inherit from this gain some convenience methods for updating
    their Justifications.
    """
    def add_support(self, reasons, weight=1.0):
        self.confidence += weight
        self.save()
        return Reason.make(self, reasons, weight, True)

    def add_oppose(self, reasons, weight=1.0):
        return Reason.make(self, reasons, weight, False)

    def confidence(self):
        return self.confidence

    def update_confidence(self):
        # TODO
        self.confidence=0
        #, confidence_update=False
        for r in Reason.objects(target=self.name):
            # Add the weight to the confidence value, should be changed to something else
            self.confidence+=r.weight
            
            # Set the reason's confidence_update value to True to ensure it won't be added again
            r.confidence_update = True
            
            self.save()
            r.save()
        return self.confidence

    def get_support(self):
        return Reason.objects(target=self.name, polarity=True)

    def get_oppose(self, dereference=True):
        return Reason.objects(target=self.name, polarity=False)

