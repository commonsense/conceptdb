import mongoengine as mon
from conceptdb import ConceptDBDocument
from conceptdb.util import ensure_reference, dereference
from log import Log
import numpy as np

def hamacher(values):
    """
    Calculates the Hamacher product of a list of numbers. The Hamacher product
    is a product-like norm that scales approximately linearly with its
    input values, so that its outputs are in the same units as its inputs.
    
    We use it for conjunctions in ConceptDB/CORONA.
    """
    result = 1.0
    for val in values:
        result = (result*val) / (result + val - result*val)
    return result

class ReasonConjunction(ConceptDBDocument, mon.Document):
    """
    A ReasonConjunction is used to connect justifications to the things they
    justify.
    
    Each ReasonConjunction represents a conjunction of multiple justifications,
    called "factors", that justify a single node called the "target". When
    there is no conjunction involved, each ReasonConjunction should simply have
    a single factor.

    ReasonConjunctions can update the reliability scores of their factors and
    their target. Over time, the update rule should converge to Rob's CORONA
    measure (the second revision, as defined in doc/corona2.tex).
    """
    # target: What is this a reason for?
    # (Expressed as a URL that may or may not refer to a DB object.)
    target = mon.StringField()

    # factors: What things must be true for this reason to be true?
    # (That is, the factors form a conjunction.)
    factors = mon.ListField(mon.StringField())

    # vote: According to this conjunction of factors, how reliable is the
    # target node?
    vote = mon.FloatField()

    # weight: How much do we believe this reason as a conjunction of
    # its factors?
    weight = mon.FloatField()

    meta = {'indexes': ['target', 'weight', 'factors']}

    @staticmethod
    def make(target, factors, vote):
        # updated to corona2 form.
        target = ensure_reference(target)
        factors = [ensure_reference(f) for f in factors]
        r, _ = ReasonConjunction.objects.get_or_create(
            target=target,
            factors__all=factors,
            defaults={'factors': factors, 'vote': vote}
        )
        if r.id is not None:
            # FIXME: this minimizes the number of factors at all costs.
            # This may not be the correct rule, but it's hard to think of
            # cases where it goes wrong.
            r.factors = factors
            r.vote = vote
        return r
    
    def update_node(self):
        prod = 1.0
        for factor_ref in self.factors:
            prod = hamacher(prod, ConfidenceValue.get(factor_ref))
        return prod

    def check_consistency(self):
        # TODO
        pass

def justify(target, factors, weight):
    return ReasonConjunction.make(target, factors, weight, True)

class ConceptDBJustified(ConceptDBDocument):
    """
    Documents that inherit from this gain some convenience methods for updating
    their Justifications.
    """
    def add_reason(self, factors, vote):
        return ReasonConjunction.make(self, factors, vote)
    
    def add_support(self, factors):
        """
        Make a ReasonConjunction that supports (votes 1 on) this object.
        """
        return self.add_reason(factors, 1.0)
    
    def add_oppose(self, factors):
        """
        Make a ReasonConjunction that opposes (votes 0 on) this object.
        """
        return self.add_reason(factors, 0.0)

    def update_confidence(self):
        """
        Update and return the confidence value of this object.
        """
        self.confidence = ConfidenceValue.calculate(self.name)
        return self.confidence

    def get_reasons(self):
        return ReasonConjunction.objects(target=self.name)

class ConfidenceValue(ConceptDBDocument, mon.Document):
    """
    The ConfidenceValue table is stored externally so that:

    - Lots of confidence values can be updated at once without sending large
      objects through an ORM.
    - We can track our confidence in objects we don't directly control, without
      having to copy them into the database.

    ConfidenceValues are never used as objects by the API. This class could be,
    and might be, replaced by some plain functions that directly operate on
    the MongoDB.
    """
    
    object_id = mon.StringField()
    confidence = mon.FloatField()

    meta = {'indexes': ['object_id', 'confidence']}
    DEFAULT_CONFIDENCE = 0.5
    DEFAULT_WEIGHT = 1.0
    
    @staticmethod
    def set(object_id, confidence):
        """
        Store the confidence value for a given ID.
        """
        query = ConfidenceValue.objects(object_id=object_id)
        query.update_one(upsert=True, safe_update=False,
                         set__confidence=confidence)
        obj = dereference(object_id)
        if obj is not None:
            obj.confidence = confidence

    @staticmethod
    def get(object_id):
        """
        Get the confidence value for a given ID.
        """
        entry = ConfidenceValue.objects.with_id(object_id)
        if entry is None:
            return ConfidenceValue.DEFAULT_CONFIDENCE
        else:
            return entry.confidence
    get_for_object = get

    @staticmethod
    def calculate(object_id):
        confidence = ConfidenceValue.DEFAULT_CONFIDENCE
        total_weight = ConfidenceValue.DEFAULT_WEIGHT
        for r in ReasonConjunction.objects(target=object_id):
            confidence += r.vote
            total_weight += r.weight
        return confidence / total_weight
