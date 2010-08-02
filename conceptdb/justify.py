import mongoengine as mon
from conceptdb import ConceptDBDocument
import numpy as np

class Justification(mon.EmbeddedDocument):
    """
    A Justification is a data structure that keeps track of evidence for
    and against a statement being correct.
    
    The evidence comes in the form of two "and/or" trees of Reasons: one
    tree of supporting reasons and one tree of opposing reasons. The trees
    are expressed as a list of lists, representing a disjunction of
    conjunctions.

    These lists of lists would be difficult to make MongoDB indices from,
    however, so internally they are expressed as two lists:

      - The *flat list* is a simple list of Reasons, without the tree
        structure.
      - The *offset list* gives *n*-1 indices into the flat list, so that
        splitting the flat list at those indices gives the *n* conjunctions.

    """
    support_flat = mon.ListField(mon.StringField()) # unevaluated Reason IDs
    oppose_flat = mon.ListField(mon.StringField())  # unevaluated Reason IDs
    support_offsets = mon.ListField(mon.IntField())
    oppose_offsets = mon.ListField(mon.IntField())
    support_weights = mon.ListField(mon.FloatField())
    oppose_weights = mon.ListField(mon.FloatField())
    confidence_score = mon.FloatField(default=0.0)

    @staticmethod
    def empty():
        """
        Get the default, empty justification.
        """
        return Justification(
            support_flat=[],
            oppose_flat=[],
            support_offsets=[],
            oppose_offsets=[],
            support_weights=[],
            oppose_weights=[],
            confidence_score=0.0
        )

    @staticmethod
    def make(support, oppose):
        """
        Make a Justification data structure from a tree of supporting reasons
        and a tree of opposing reasons.

        support and oppose inputs consist of a list of lists of (ReasonID,
        weight) tuples. Method flattens them into mongodb friendly formats.
        """
        # TODO: implement confidence scores
        support_flat = []
        oppose_flat = []
        support_offsets = []
        oppose_offsets = []
        support_weights = []
        oppose_weights = []
        
        #go through support and oppose lists, building offsets, weights, flat
        for l in support:
            if(len(support_offsets) == 0):
                support_offsets.append(len(l))
            elif (len(support_offsets) == len(support) - 1):
                pass #don't need to add last
            else:
                support_offsets.append(len(l) + support_offsets[-1])
            flat, weight = zip(*l)
            support_flat.extend(flat)
            support_weights.extend(weight)

        for l in oppose:
            if(len(oppose_offsets) == 0):
                oppose_offsets.append(len(l))
            elif (len(oppose_offsets) == len(oppose) - 1):
                pass
            else:
                oppose_offsets.append(len(l) + oppose_offsets[-1]) 
            flat, weight = zip(*l)
            oppose_flat.extend(flat)
            oppose_weights.extend(weight)

        #I assume that since Justifications are embedded documents, there is no
        #need to search for a duplicate before creating them?
        j = Justification(
            support_flat = support_flat,
            oppose_flat = oppose_flat,
            support_offsets = support_offsets,
            oppose_offsets = oppose_offsets,
            support_weights = support_weights,
            oppose_weights = oppose_weights
            )
        j.update_confidence()
        return j
    
    def update_confidence(self):
        # Calculate a conservative probabilistic estimate of confidence:
        # the probability that the support is correct *and* the opposition is
        # incorrect.
        self.confidence_score = self.compute_confidence(self.get_support()) * (1.0 - self.compute_confidence(self.get_oppose()))
        return self.confidence_score

    def compute_confidence(self, disjunction):
        # Compute using probabilities. This may or may not turn out to be the
        # right idea.
        inv_prob = 1.0
        for conjunction in disjunction: # what's your function
            prob = 1.0
            for reason, weight in conjunction:
                confidence = np.clip(reason.confidence_score, 0, 1) * np.clip(weight, 0, 1)
                prob *= confidence
            inv_prob *= (1.0 - prob)
        return (1.0 - inv_prob)

    def check_consistency(self):
        for offset in self.support_offsets:
            assert offset < len(self.support_flat)
        for offset in self.oppose_offsets:
            assert offset < len(self.oppose_flat)
        for reason in self.support_flat:
            lookup_reason(reason)
        for reason in self.oppose_flat:
            lookup_reason(reason)
        assert len(self.support_flat) == len(self.support_weights)
        assert len(self.oppose_flat) == len(self.oppose_weights)
        assert self.confidence_score >= 0.0
        assert self.confidence_score <= 1.0

    def add_conjunction(self, reasons, flatlist, offsetlist, weightlist):
        # FIXME: if a conjunction is added with the same reasons but different
        # weights as another, it should be updated instead.
        def transform_reason(r):
            if isinstance(r, tuple):
                reason, weight = r
            else:
                reason = r
                weight = 1.0
            if isinstance(reason, ConceptDBDocument):
                reason = reason.name
            assert isinstance(reason, basestring)
            return (reason, weight)

        weighted_reasons = [transform_reason(r) for r in reasons]
        dis = self.get_disjunction(flatlist, offsetlist, weightlist)
        if weighted_reasons in dis: return self

        offset = len(flatlist)
        reasons = [reason for reason, weight in weighted_reasons]
        weights = [weight for reason, weight in weighted_reasons]
        flatlist.extend(reasons)
        weightlist.extend(weights)
        offsetlist.append(offset)
        return self

    def add_support(self, reasons):
        assert reasons
        return self.add_conjunction(reasons, self.support_flat, self.support_offsets, self.support_weights)

    def add_opposition(self, reasons):
        return self.add_conjunction(reasons, self.oppose_flat, self.oppose_offsets, self.oppose_weights)
    
    def get_disjunction(self, flatlist, offsetlist, weightlist):
        disjunction = []
        flatlist = [lookup_reason(x) for x in flatlist]
        if offsetlist:
            prev_offset = offsetlist[0]
            for offset in offsetlist[1:]:
                disjunction.append(zip(flatlist[prev_offset:offset],
                                       weightlist[prev_offset:offset]))
                prev_offset = offset
            disjunction.append(zip(flatlist[prev_offset:],
                                   weightlist[prev_offset:]))
        return disjunction
    
    def get_support(self):
        return self.get_disjunction(self.support_flat, self.support_offsets,
                                    self.support_weights)

    def get_opposition(self):
        return self.get_disjunction(self.oppose_flat, self.oppose_offsets,
                                    self.oppose_weights)
    
    # Aliases
    add_oppose = add_opposition
    get_oppose = get_opposition

class ConceptDBJustified(ConceptDBDocument):
    """
    Documents that inherit from this gain some convenience methods for updating
    their Justifications.
    """
    def add_support(self, reasons):
        self.justification = self.justification.add_support(reasons)

    def add_oppose(self, reasons):
        self.justification = self.justification.add_oppose(reasons)

def lookup_reason(reason):
    from conceptdb.metadata import ExternalReason
    if isinstance(reason, ConceptDBDocument):
        return reason
    else:
        assert isinstance(reason, basestring)
        if reason.startswith('/assertion/'):
            from conceptdb.assertion import Assertion
            parts = reason.split('/')
            a_id = parts[2]
            assertion = Assertion.objects.with_id(a_id)
            return assertion
        elif reason.startswith('/data/'):
            return ExternalReason.objects.with_id(reason)
        else:
            raise NameError("I don't know what kind of reason %s is" % reason)

