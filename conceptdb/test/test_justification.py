from conceptdb.justify import Justification
import conceptdb
from conceptdb.metadata import Dataset, ExternalReason

conceptdb.connect_to_mongodb('test')

def test_justification():
    ExternalReason.drop_collection()
    Dataset.drop_collection()

    #create empty justification
    empty = Justification.empty()

    #make sure empty justification passes consistency checks
    empty.check_consistency()
    dataset = Dataset.make('/data/test', 'en')
    root = dataset.get_root_reason()

    #create dummy reasons (needed for consistency check)
    reasons = []
    for i in xrange(0,21):
        reasons.append(root.derived_reason('/reason%d' % i, 1.0 - (.01*i)))

    for i in xrange(0,21):
        assert reasons[i].confidence() == 1.0 - (.01*i)
           
    #create support/oppose lists of lists, inner lists (string, float) tuples
    #representing reason IDs and weights

    support = [[(reasons[1], 0.5), (reasons[2], 0.5), (reasons[3], 0.5)],
               [(reasons[4], 0.5), (reasons[5], 0.5), (reasons[6], 0.5), (reasons[7], 0.5)],
               [(reasons[8], 0.5), (reasons[9], 0.5)]]
    oppose = [[(reasons[10], 0.5), (reasons[11], 0.5), (reasons[12], 0.5)],
              [(reasons[13], 0.5), (reasons[14], 0.5)]]
    
    #make a Justification with above support oppose trees
    j = Justification.make(support, oppose)

    #check its consistency
    j.check_consistency()
    
    #make sure flattened list components match expected
    assert j.support_flat == ["/data/test/reason%d" % i for i in xrange(1,10)]
    assert j.oppose_flat == ["/data/test/reason%d" % i for i in xrange(10,15)]

    assert j.support_offsets == [0, 3, 7]
    assert j.support_weights == [0.5]*9
    
    assert j.oppose_offsets == [0, 3]
    assert j.oppose_weights == [0.5]*5

    #make sure get_support, get_opposition equal original 
    assert j.get_support() == support
    assert j.get_opposition() == oppose
    
    #add an identical clause and make sure the justification is unchanged
    j.add_support([(reasons[1], 0.5), (reasons[2],0.5),(reasons[3],0.5)])
    assert j.support_flat == ["/data/test/reason%d" % i for i in xrange(1,10)]
    assert j.support_offsets == [0, 3, 7]
    assert j.support_weights == [0.5]*9
    assert j.get_support() == support

    #add a clause with the same reasons but different weights and make sure
    #that only the weights change
    j.add_support([(reasons[8], 0.5), (reasons[9], 0.6)])
    assert j.support_flat == ["/data/test/reason%d" % i for i in xrange(1,10)]
    assert j.support_offsets == [0, 3, 7]
    assert j.support_weights == [0.5]*8 + [0.6]

    #change it back for confidence score test
    j.add_support([(reasons[8], 0.5), (reasons[9], 0.5)])

    #add new support and oppose clauses
    newSupport = [(reasons[15], 0.5), (reasons[16], 0.5), (reasons[17], 0.5)]
    newOppose  = [(reasons[18], 0.5), (reasons[19], 0.5), (reasons[20], 0.5)]
    j.add_support(newSupport)
    j.add_oppose(newOppose)

    #make sure flattened list components match expected
    assert j.support_flat == (["/data/test/reason%d" % i for i in xrange(1,10)]
      + ["/data/test/reason%d" % i for i in xrange(15, 18)])
    assert j.oppose_flat == (["/data/test/reason%d" % i for i in xrange(10,15)]
      + ["/data/test/reason%d" % i for i in xrange(18, 21)])
    assert j.support_offsets == [0,3,7,9]
    assert j.support_weights == [0.5]*12
    assert j.oppose_offsets == [0,3,5]
    assert j.oppose_weights == [0.5]*8

    # NOTE: Change these if the method of computing confidence changes.
    assert 0.38 < j.compute_confidence(j.get_support()) < 0.39
    assert 0.30 < j.compute_confidence(j.get_oppose()) < 0.31
    assert 0.26 < j.confidence_score < 0.27

    #make sure get_support, get_opposition return correctly
    support.append(newSupport)
    oppose.append(newOppose)
    assert j.get_support() == support
    assert j.get_opposition() == oppose

    #clean up
    ExternalReason.drop_collection()
    Dataset.drop_collection()
