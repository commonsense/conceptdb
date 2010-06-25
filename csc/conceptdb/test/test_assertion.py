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

 
    
