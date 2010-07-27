from conceptdb.assertion import Assertion
from conceptdb.expression import Expression
from conceptdb.metadata import Dataset
import conceptdb

conceptdb.connect_to_mongodb('test')

def test_expression():
    Assertion.drop_collection() 
    
    a1 = Assertion.make('/data/test','/rel/IsA',
                        ['/concept/test/assertion', '/concept/test/test'])
    expr = a1.add_expression(
      Expression.make('{0} is a {1}', ['this assertion', 'test'], 'en')
    )
    
    # load the same assertion from the DB
    a2 = Assertion.make('/data/test','/rel/IsA',
                        ['/concept/test/assertion', '/concept/test/test'])
    assert len(a2.expressions) == 1
    assert a2.expressions[0].text == "this assertion is a test"

    Assertion.drop_collection() 
