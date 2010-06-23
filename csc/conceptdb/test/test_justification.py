from csc.conceptdb.justify import Justification
from csc import conceptdb
from csc.conceptdb.metadata import Dataset

def test_justification():
    
    #create support/oppose lists of lists, inner lists (string, float) tuples representing
    #reason IDs and weights

    support = [[("reason1", 0.1), ("reason2", 0.2), ("reason3", 0.3)], [("reason4", 0.4), 
                ("reason5", 0.5), ("reason6", 0.6), ("reason7", 0.7)], [("reason8", 0.8), 
                ("reason9", 0.9)]]

    oppose = [[("reason10", 0.10), ("reason11", 0.11), ("reason12", 0.12)], [("reason13", 0.13),
            ("reason14", 0.14)]]

    #make a Justification with above support oppose trees

    j = Justification.make(support, oppose)

    #check its consistency
    #j.check_consistency()
    
    #make sure flattened list components match expected
    assert j.support_flat == ["reason1", "reason2", "reason3", "reason4", "reason5", "reason6",
                                "reason7", "reason8", "reason9"]
    assert j.support_offsets == [3, 7]
    assert j.support_weights == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    assert j.oppose_flat == ["reason10", "reason11", "reason12", "reason13", "reason14"]
    assert j.oppose_offsets == [3]
    assert j.oppose_weights == [0.10, 0.11, 0.12, 0.13, 0.14]

    
