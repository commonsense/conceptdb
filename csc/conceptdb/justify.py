import mongoengine as mon

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

        support and oppose inputs consist of a list of lists of (ReasonID, weight) tuples.  
        Method flattens them into mongodb friendly formats.
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
        return j
            
    def check_consistency(self):
        for offset in self.support_offsets:
            assert offset < len(self.support_flat)
        for offset in self.oppose_offsets:
            assert offset < len(self.oppose_flat)
        for reason in self.support_flat:
            #support flat stores reason IDs, not reason objects.  Check for presence in DB?
            Reason.objects.get(reason)
        for reason in self.oppose_flat:
            Reason.objects.get(reason)
        assert len(self.support_flat) == len(self.support_weights)
        assert len(self.oppose_flat) == len(self.oppose_weights)

        #TODO: will confidence score be in a given range?  Could be additional consistency check

    def add_conjunction(self, weighted_reasons, flatlist, offsetlist, weightlist):
        offset = len(flatlist)
        reasons = [reason for reason, weight in weighted_reasons]
        weights = [weight for reason, weight in weighted_reasons]
        flatlist.extend(reasons)
        weightlist.extend(weights)
        offsetlist.append(offset)
        return self

    def add_support(self, reasons):
        return self.add_conjunction(reasons, self.support_flat, self.support_offsets, self.support_weights)

    def add_opposition(self, reasons):
        return self.add_conjunction(reasons, self.oppose_flat, self.oppose_offsets, self.oppose_weights)
    
    def get_disjunction(self, flatlist, offsetlist, weightlist):
        disjunction = []
        prev_offset = 0
        for offset in offsetlist:
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

class Reason(mon.Document):
    name = mon.StringField(required=True, primary_key=True)
    type = mon.StringField(required=True)
    reliability = mon.FloatField(default=0.0)
    justification = mon.EmbeddedDocumentField(Justification)
