from conceptdb.assertion import Assertion, Expression
from conceptdb.metadata import Dataset
import conceptdb

conceptdb.connect_to_mongodb('test')

def test_assertion():
    # fresh start
    Dataset.drop_collection()
    Assertion.drop_collection()
    
    #create test dataset
    dataset = Dataset.create(language = 'en', name = '/data/test')

    #make a test assertion
    a1 = Assertion.make('/data/test',"/rel/IsA",["/concept/test/assertion", "/concept/test/test"])
    e = Expression.make(a1, "{0} is a {1}", ['this assertion', 'test'], 'en')
    print e.assertion
    e.add_support([dataset.get_root_reason()])
    a1.add_support([dataset.get_root_reason()])
    a1.save()
    a1.make_generalizations('/data/test/root')
    a2 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="/concept/test/assertion,/concept/test/test"
    )
    print a1.get_expressions()
    assert a2.get_expressions()[0].text == 'this assertion is a test'

    a3 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="/concept/test/assertion,*"
    )
    assert a3.get_expressions()[0].text == 'this assertion is a {1}'
    
    a4 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="*,/concept/test/test"
    )
    assert a4.get_expressions()[0].text == '{0} is a test'
    
    a5 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="*,*"
    )
    assert a5.get_expressions()[0].text == '{0} is a {1}'
    
    #clean up
    Dataset.drop_collection()
    Assertion.drop_collection()
 
