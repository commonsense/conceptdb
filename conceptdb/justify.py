import mongoengine as mon
from conceptdb import ConceptDBDocument, to_json
from log import Log
import numpy as np

def ensure_reference(obj):
    if isinstance(obj, basestring): return obj
    elif isinstance(obj, ConceptDBDocument): return obj.name
    else:
        raise ValueError("Don't know how to reference %s" % obj)

def ensure_weight(obj):
    if not isinstance(obj, tuple):
        return (obj, 1.0)
    else:
        assert len(obj) == 2
        return obj

class Reason(ConceptDBDocument, mon.Document):
    # target: What is this a reason for?
    # (Expressed as a URL that may or may not refer to a DB object.)
    target = mon.StringField()

    # factors: What things must be true for this reason to be true?
    # (That is, the factors form a conjunction.)
    factors = mon.ListField(mon.StringField())

    # weights: How much support does this reason have from each of its factors?
    weights = mon.ListField(mon.FloatField())

    # polarity: Is this a reason to believe or disbelieve its target?
    polarity = mon.BooleanField()

    meta = {'indexes': [('target', 'polarity'),
                        'factors']}

    @staticmethod
    def make(target, weighted_factors, polarity):
        target = ensure_reference(target)
        weighted_factors = [ensure_weight(wf) for wf in weighted_factors]
        factors = [ensure_reference(wf[0]) for wf in weighted_factors]
        weights = [wf[1] for wf in weighted_factors]
        r = Reason.objects.get_or_create(
            target=target,
            factors__all=factors,
            polarity=polarity,
            defaults={'factors': factors, 'weights': weights}
        )
        if r.id is not None:
            # FIXME: this minimizes the number of factors at all costs.
            # Occam's supercharged electric razor may not be exactly the right
            # criterion.
            r.factors = factors
            r.weights = weights
        return r

    def check_consistency(self):
        assert len(self.factors) == len(self.weights)

def justify(target, weighted_factors):
    return Reason.make(target, weighted_factors, True)

class ConceptDBJustified(ConceptDBDocument):
    """
    Documents that inherit from this gain some convenience methods for updating
    their Justifications.
    """
    def add_support(self, reasons):
        return Reason.make(self, reasons, True)

    def add_oppose(self, reasons):
        return Reason.make(self, reasons, False)

    def confidence(self):
        return self.confidence

    def update_confidence(self):
        # TODO
        pass

    def get_support(self):
        return Reason.objects(target=self.name, polarity=True)

    def get_oppose(self, dereference=True):
        return Reason.objects(target=self.name, polarity=False)

