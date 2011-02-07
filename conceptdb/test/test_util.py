from conceptdb.util import *

def test_outer_iter():
    input = [('a'), ('b', 'c'), ('d', 'e', 'f')]
    output = [''.join(seq) for seq in outer_iter(input)]
    assert len(output) == 6
    assert 'abd' in output
    assert 'abe' in output
    assert 'abf' in output
    assert 'acd' in output
    assert 'ace' in output
    assert 'acf' in output
    
    input = [('a'), (), ('d', 'e', 'f')]
    output = list(outer_iter(input))
    assert output == []
