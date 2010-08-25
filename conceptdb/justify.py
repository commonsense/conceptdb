import mongoengine as mon
from conceptdb import ConceptDBDocument
import numpy as np

def transform_reason(r, dereference=False):
    """
    transform_reason accepts inputs of the form (reasonname, weight),
    reasonname, (ConceptDBJustified, weight) and ConceptDBJustified
    and returns (reasonname, weight).  If no weight was given in 
    the input the weight defaults to 1.0.  
    """
    if isinstance(r, tuple):
        r2, weight = r
    else:
        r2 = r
        weight = 1.0
    if isinstance(r2, ConceptDBJustified):
        reason = r2
        rname = r2.name
    else:
        if dereference: reason = lookup_reason(r2)
        rname = r2
    
    if dereference:
        assert isinstance(reason, ConceptDBJustified)
        return (reason, weight)
    assert isinstance(rname, basestring)
    return (rname, weight)

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

        support_flat = []
        oppose_flat = []
        support_offsets = []
        oppose_offsets = []
        support_weights = []
        oppose_weights = []
        
        support = [[transform_reason(r) for r in sub] for sub in support]
        oppose = [[transform_reason(r) for r in sub] for sub in oppose]

        #go through support and oppose lists, building offsets, weights, flat
        support_index = 0
        for l in support:
            support_offsets.append(support_index)
            support_index += len(l)
            flat, weight = zip(*l)
            support_flat.extend(flat)
            support_weights.extend(weight)

        oppose_index = 0
        for l in oppose:
            oppose_offsets.append(oppose_index)
            oppose_index += len(l)
            flat, weight = zip(*l)
            oppose_flat.extend(flat)
            oppose_weights.extend(weight)
        #create justification
        j = Justification(
            support_flat = support_flat,
            oppose_flat = oppose_flat,
            support_offsets = support_offsets,
            oppose_offsets = oppose_offsets,
            support_weights = support_weights,
            oppose_weights = oppose_weights
        )
        j.update_confidence() #calculate confidence score
        return j
    
    def update_confidence(self):
        # Calculate a conservative probabilistic estimate of confidence:
        # the probability that the support is correct *and* the opposition is
        # incorrect.
        self.confidence_score = self.compute_confidence(self.get_support()) * (1.0 - self.compute_confidence(self.get_oppose()))
        return self

    def compute_confidence(self, disjunction):
        # Compute using probabilities. This may or may not turn out to be the
        # right idea.
        inv_prob = 1.0
        for conjunction in disjunction: # what's your function
            inv_prob *= (1.0 - self._conjunction_confidence(conjunction))
        return (1.0 - inv_prob)

    def _conjunction_confidence(self, conjunction):
        prob = 1.0
        for reason, weight in conjunction:
            confidence = np.clip(reason.confidence(), 0, 1) * np.clip(weight, 0, 1)
            prob *= confidence
        return prob

    def increase_confidence(self, conjunction):
        # untested and doesn't seem to work correctly
        self.confidence_score = 1.0 - (1.0-self.confidence_score) * (1.0-self._conjunction_confidence(conjunction))
        raise NotImplementedError

    def decrease_confidence(self, conjunction):
        # untested and doesn't seem to work correctly
        self.confidence_score = self.confidence_score * (1.0-self._conjunction_confidence(conjunction))
        raise NotImplementedError

    def check_consistency(self):
        for offset in self.support_offsets:
            assert offset < len(self.support_flat)
        for offset in self.oppose_offsets:
            assert offset < len(self.oppose_flat)
        for reason in self.support_flat:
            assert isinstance(reason, basestring)
            lookup_reason(reason)
        for reason in self.oppose_flat:
            assert isinstance(reason, basestring)
            lookup_reason(reason)
        if self.support_offsets: assert self.support_offsets[0] == 0
        if self.oppose_offsets: assert self.oppose_offsets[0] == 0
        assert len(self.support_flat) == len(self.support_weights)
        assert len(self.oppose_flat) == len(self.oppose_weights)
        assert self.confidence_score >= 0.0
        assert self.confidence_score <= 1.0

    def add_conjunction(self, reasons, flatlist, offsetlist, weightlist):

        weighted_reasons = [transform_reason(r) for r in reasons]
        dis = self.get_disjunction(flatlist, offsetlist, weightlist, dereference=False)

        #if the exact clause to be added already exists in dis, do nothing
        if weighted_reasons in dis: return False

        #check for conjunction with same reasons but different weights
        #if there is one, update the weights but do not add new conjunction
        offset = len(flatlist)
        reasons = [reason for reason, weight in weighted_reasons]
        weights = [weight for reason,weight in weighted_reasons]

        for i, conj in enumerate(dis):
            if reasons == [reason for reason,weight in conj]:
                off1 = offsetlist[i]
                #update that conjunction only
                if i == len(dis) - 1:
                    off2 = offset
                else:
                    off2 = offsetlist[i + 1]
                weightlist[off1:off2] = weights
                return True

        #if the conjunction of reasons does not exist in the disjunction, add it
        flatlist.extend(reasons)
        weightlist.extend(weights)
        offsetlist.append(offset)
        return True

    def add_support(self, reasons):
        """
        add_support takes a conjunction given as a list of reasons as an argument
        and adds it to the and/or tree for the support.
        """
        assert isinstance(reasons,list) #NOTE:get weird behavior when added reason outright accidentally
        self.add_conjunction(reasons, self.support_flat, self.support_offsets, self.support_weights)
        return self

    def add_opposition(self, reasons):
        """
        add_opposition takes a conjunction given as a list of reasons as an argument
        and adds it to the and/or tree for the opposition.
        """
        assert isinstance(reasons,list) #NOTE:get weird behavior when added reason outright
        self.add_conjunction(reasons, self.oppose_flat, self.oppose_offsets, self.oppose_weights)
        return self
    
    def get_disjunction(self, flatlist, offsetlist, weightlist, dereference=True):
        disjunction = []
        if dereference:
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
    
    def get_support(self, dereference=True):
        return self.get_disjunction(self.support_flat, self.support_offsets,
                                    self.support_weights, dereference)

    def get_opposition(self, dereference=True):
        return self.get_disjunction(self.oppose_flat, self.oppose_offsets,
                                    self.oppose_weights, dereference)
    
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
        self.save()

    def add_oppose(self, reasons):
        self.justification = self.justification.add_oppose(reasons)
        self.save()

    def confidence(self):
        return self.justification.confidence_score

    def update_confidence(self):
        self.justification.update_confidence()

    def get_support(self, dereference=True):
        return self.justification.get_support(dereference)

    def get_oppose(self, dereference=True):
        return self.justification.get_oppose(dereference)

def lookup_reason(reason):
    from conceptdb.metadata import ExternalReason
    if isinstance(reason, ConceptDBJustified):
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
            ext = ExternalReason.objects.with_id(reason)
            return ext
        elif reason.startswith('/expression'):
            from conceptdb.assertion import Assertion, Expression
            parts = reason.split('/')
            a_id = parts[2]
            e_id = parts[3]
            assertion = Assertion.objects.with_id(a_id)
            expression = assertion.expression_with_id(e_id)
            return expression
        else:
            raise NameError("I don't know what kind of reason %s is" % reason)

