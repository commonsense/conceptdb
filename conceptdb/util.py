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

