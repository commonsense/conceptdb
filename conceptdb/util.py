from conceptdb import ConceptDBDocument, to_json

def ensure_reference(obj):
    """
    Take in an object and get a string representing its ID. If it's already
    an ID string, leave it alone.
    """
    if isinstance(obj, basestring):
        return obj
    elif isinstance(obj, ConceptDBDocument):
        return obj.name
    else:
        raise ValueError("Don't know how to reference %s" % obj)

def outer_iter(seqs):
    """
    Gives an iterator over the outer product of a number of sequences.
    """
    if len(seqs) == 0:
        yield ()
        return
    else:
        head = seqs[0]
        tail = seqs[1:]
        for tailseq in outer_iter(tail):
            for item in head:
                yield (item,) + tailseq

def dereference(id):
    """
    Get the ConceptDBJustified object corresponding to an ID, if possible.
    """
    from conceptdb import assertion
    cls = None
    if id.startswith('/assertion'):
        cls = assertion.Assertion
    elif id.startswith('/expression'):
        cls = assertion.Expression
    elif id.startswith('/sentence'):
        cls = assertion.Sentence
    else:
        return None
    
    return cls.objects.with_id(id)

