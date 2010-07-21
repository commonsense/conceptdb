from csc import conceptdb
from csc.conceptdb.justify import Reason
from csc.conceptdb.justify import Justification

conceptdb.connect_to_mongodb('test')

def test_reason():

    reason = Reason.create(name="test_reason", type = "test_type")

    #make sure it exists in the DB
    assert reason.id is not None

    #make sure its attributes are readable
    reason.name
    reason.type

    #clean up
    Reason.drop_collection()    
