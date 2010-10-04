from conceptdb.assertion import Assertion, Expression
from conceptdb.metadata import Dataset
import conceptdb

conceptdb.connect_to_mongodb('test')

def test_expression():

    #start clean
    Expression.drop_collection()
    Assertion.drop_collection() 
    
    a1 = Assertion.make('/data/test','/rel/IsA',
                        ['/concept/test/assertion', '/concept/test/test'])
   
    expr = Expression.make(a1, '{0} is a {1}', ['this assertion', 'test'], 'en')
    
    #check for consistency, ensure all attributes are readable
    expr.check_consistency()
    expr.assertion
    expr.text
    expr.confidence
    expr.arguments
    expr.language
    expr.frame
    expr.id

    assert expr.name == '/expression/%s' % expr.id

    # load the same assertion from the DB
    a2 = Assertion.make('/data/test','/rel/IsA',
                        ['/concept/test/assertion', '/concept/test/test'])
    assert expr.assertion == a2


    #test static methods
    replace = Expression.replace_args(expr.frame, expr.arguments)
    assert replace == "this assertion is a test"

    #clean up
    Assertion.drop_collection() 
    Expression.drop_collection()
