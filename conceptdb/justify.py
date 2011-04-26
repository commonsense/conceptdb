import mongoengine as mon
from conceptdb import ConceptDBDocument, to_json
from log import Log
import numpy as np

def ensure_reference(obj):
    if isinstance(obj, basestring): return obj
    elif isinstance(obj, ConceptDBDocument): return obj.name
    else:
        raise ValueError("Don't know how to reference %s" % obj)

def hamacher(values):
    """
    Calculates the Hamacher product of a list of numbers. The Hamacher product
    is a product-like norm that scales approximately linearly with its
    input values. We use it for conjunctions in ConceptDB/CORONA.
    """
    result = 1.0
    for val in values:
        result = (result*val) / (result + val - result*val)
    return result

class Reason(ConceptDBDocument, mon.Document):
    """
    A Reason is used to connect justifications to the things they justify.
    
    Each Reason represents a conjunction of multiple justifications, called
    "factors", that justify a single node called the "target". When there is
    no conjunction involved, each Reason should simply have a single factor.

    Reasons can update the reliability scores of their factors and their
    target. Over time, the update rule should converge to Rob's CORONA measure
    (the second revision, as defined in doc/corona2.tex).
    """
    # target: What is this a reason for?
    # (Expressed as a URL that may or may not refer to a DB object.)
    target = mon.StringField()

    # factors: What things must be true for this reason to be true?
    # (That is, the factors form a conjunction.)
    factors = mon.ListField(mon.StringField())

    # edge_weight: How much do we inherently believe this reason, independently
    # of how much we believe its factors?
    edge_weight = mon.FloatField()

    # node_weight: How much do we believe this reason as a conjunction of
    # its factors?
    node_weight = mon.FloatField()

    meta = {'indexes': ['target', 'node_weight', 'factors']}

    @staticmethod
    def make(target, factors, weight, polarity):
        target = ensure_reference(target)
        factors = [ensure_reference(f) for f in factors]
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
            r[0].edge_weight = weight
            r[0].node_weight = 0.0
            r[0].update_node()
        return r[0]
    
    def update_node(self):
        pass

    def check_consistency(self):
        assert 0.0 <= self.node_weight <= 1.0
        assert 0.0 <= self.edge_weight <= 1.0

def justify(target, factors, weight):
    return Reason.make(target, factors, weight, True)

class ConceptDBJustified(ConceptDBDocument):
    """
    Documents that inherit from this gain some convenience methods for updating
    their Justifications.
    """
    def add_support(self, reasons, weight=1.0):
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

