from csc.conceptdb.assertions import Assertion
from csc.conceptdb.metadata import Dataset
from csc import conceptdb

conceptdb.connect_to_mongodb('test')

def test_assertion():
    
    #create test dataset
    dataset = Dataset.create(language = 'en', name = 'test/dataset test')

    #make a test assertion
    a1 = Assertion.make('test/dataset test',"isA",["assertion", "test"])

    #verify that it exists in the database
    assert a1.id is not None

    #make sure attributes are readable
    a1.dataset
    a1.relation
    a1.arguments
    a1.argstr
    a1.complete
    a1.context
    a1.polarity
    a1.expressions
    a1.justification    

    #make an identical test assertion
    a2 = Assertion.make('test/dataset test',"isA",["assertion", "test"])

    #verify that it exists in the database
    assert a2.id is not None
    print a2.id
    print a1.id
    
    #verify that attributes are readable
    a2.dataset
    a2.relation
    a2.arguments
    a2.argstr
    a2.complete
    a2.context
    a2.polarity
    a2.expressions
    a2.justification
    print ("about to check")
    #check that all checked attributes are the same
    assert a1.dataset == a2.dataset
    assert a1.relation == a2.relation
    assert a1.arguments == a2.arguments
    assert a1.polarity == a2.polarity
    assert a1.context == a2.context

    #verify that the ID's are the same
    assert (a1.id == a2.id)

    #clean up
    Dataset.drop_collection()
    Assertion.drop_collection() 
 
    
