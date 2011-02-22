from conceptdb.freebase_imports import MQLQuery
from conceptdb.assertion import Assertion
import freebase

import conceptdb

conceptdb.connect_to_mongodb('test')

def test_freebase_allresults():
    Assertion.drop_collection()
    
    query_args = {'id':'/en/the_beatles', 'type':'/music/artist'}
    result_args = ['*']
    
    q = MQLQuery.make(query_args, result_args)
    
    q.get_results('/data/test')
    
    for a in Assertion.objects:
        print str(a.arguments)
        print str(a.relation)
    
    Assertion.drop_collection()
    
def test_freebase_resargs():
    Assertion.drop_collection()
    
    query_args = {'id':'/en/the_beatles'}
    result_args = ['*']
    
    q = MQLQuery.make(query_args, result_args)
    
    q.get_results('/data/test')
    
    
    for a in Assertion.objects:
        print str(a.arguments)
        print str(a.relation)
    
    Assertion.drop_collection()

def test_get_props():
    q = MQLQuery.make({'id':'/en/the_beatles','type':'/music/artist'}, ['*'])
    
    print q.view_props()
        
def test_get_entities():
    property = 'type'
    
    q = MQLQuery.make({'id':'/en/the_beatles','type':'/music/artist'}, ['*'])
    
    print q.view_entities(property)
    
def test_import_all():
    
    Assertion.drop_collection()
    
    q = MQLQuery.make({'id':'/en/the_beatles'}, ['*'])
    
    assertions = q.get_results('/data/test',1,None,'nholm',True)
    
    for a in Assertion.objects:
        print a.relation
#
#    mss = freebase.HTTPMetawebSession('http://api.freebase.com')
#    
#    query = [{"*":{},"id":"/en/the_beatles","type":"/music/artist"}]
#    
#    results = mss.mqlread(query)
#    
#    print results

    
    Assertion.drop_collection()
    
    
test_import_all()
    
       