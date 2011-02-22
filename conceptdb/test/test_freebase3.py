from conceptdb.freebase_imports import MQLQuery
from conceptdb.assertion import Assertion, Sentence, Expression
from conceptdb.metadata import Dataset
import freebase
import conceptdb
from csc.conceptnet.models import User
from conceptdb.justify import Reason
from piston.utils import throttle, rc
from mongoengine.queryset import DoesNotExist
from freebase.api.session import MetawebError, HTTPMetawebSession

conceptdb.connect_to_mongodb('test')

def test_freebase_allresults():
    Assertion.drop_collection()
    Sentence.drop_collection()
    Expression.drop_collection()
    Dataset.drop_collection()
    
    
    query_args = {'id':'/en/the_beatles', 'type':'/music/artist'}
    result_args = ['*']
    
    q = MQLQuery.make(query_args, result_args)
    
    q.get_results('/data/test')
    
    
    for s in Sentence.objects:
        print s.text
    
    for a in Assertion.objects:
        print str(a.arguments)
        print str(a.relation)
    
    Assertion.drop_collection()
    Sentence.drop_collection()
    Expression.drop_collection()
    Dataset.drop_collection()
    
def test_freebase_resargs():
    Assertion.drop_collection()
    Sentence.drop_collection()
    Expression.drop_collection()
    Dataset.drop_collection()
    
    
    query_args = {'id':'/en/the_beatles'}
    result_args = ['*']
    
    q = MQLQuery.make(query_args, result_args)
    
    q.get_results('/data/test')
    
    
    for s in Sentence.objects:
        print s.text
    
    for a in Assertion.objects:
        print str(a.arguments)
        print str(a.relation)
    
    Assertion.drop_collection()
    Sentence.drop_collection()
    Expression.drop_collection()
    Dataset.drop_collection()
    
def test_get_props():
    q = MQLQuery.make({'id':'/en/the_beatles','type':'/music/artist'}, ['*'])
    
    print q.view_props()
        
def test_get_entities():
    property = 'type'
    
    q = MQLQuery.make({'id':'/en/the_beatles','type':'/music/artist'}, ['*'])
    
    print q.view_entities(property)
    
    
test_get_props()
    
       