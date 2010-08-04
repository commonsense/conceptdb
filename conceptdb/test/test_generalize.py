from conceptdb.assertion import Assertion
from conceptdb.expression import Expression
from conceptdb.metadata import Dataset, ExternalReason
import conceptdb

conceptdb.connect_to_mongodb('test')

def test_assertion():
    # fresh start
    Dataset.drop_collection()
    Assertion.drop_collection()
    ExternalReason.drop_collection()
    
    #create test dataset
    dataset = Dataset.create(language = 'en', name = '/data/test')

    #make a test assertion
    e = Expression.make("{0} is a {1}", ['this assertion', 'test'], 'en')
    e.add_support([dataset.get_root_reason()])
    a1 = Assertion.make('/data/test',"/rel/IsA",["/concept/test/assertion", "/concept/test/test"], expressions=[e])
    assert len(a1.justification.get_support()) == 0
    a1.add_support([dataset.get_root_reason()])
    assert len(a1.justification.get_support()) == 1
    a1.save()
    a1.make_generalizations()
    a2 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="/concept/test/assertion,/concept/test/test"
    )
    assert a2.expressions[0].text == 'this assertion is a test'
    assert a2.justification.get_support()[0][0][0] == dataset.get_root_reason()

    a3 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="/concept/test/assertion,*"
    )
    assert a3.expressions[0].text == 'this assertion is a {1}'
    assert a3.justification.get_support()[0][1][0] == a1
    assert a3.expressions[0].justification.get_support()[0][2][0] == dataset.get_root_reason()
    
    a4 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="*,/concept/test/test"
    )
    assert a4.expressions[0].text == '{0} is a test'
    
    a5 = Assertion.objects.get(
        dataset='/data/test',
        relation='/rel/IsA',
        argstr="*,*"
    )
    assert a5.expressions[0].text == '{0} is a {1}'
    
    #clean up
    Dataset.drop_collection()
    Assertion.drop_collection()
    ExternalReason.drop_collection()
 
