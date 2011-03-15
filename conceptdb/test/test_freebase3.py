from conceptdb.freebase_imports import MQLQuery
from conceptdb.assertion import Assertion
from conceptdb.metadata import Dataset
from mongoengine.queryset import DoesNotExist
import freebase

import conceptdb

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
    
    print MQLQuery.view_props(q.query_args)
        
def test_get_entities():
    property = 'type'
    
    q = MQLQuery.make({'id':'/en/the_beatles','type':'/music/artist'}, ['*'])
    
    print MQLQuery.view_entities(q.query_args, property)
    
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
    
def test_create_or_vote():
    q = MQLQuery.make({'id':'/en/the_beatles'}, ['*'])
    
    Assertion.drop_collection()
    
    assertions = q.get_results('/data/test','nholm', 1,None,False)
    
    print str(len(assertions))
    
    assertions2 = q.get_results('/data/test','nholm', 1,None,False)
    
    print str(len(assertions2))
    count = 0
    for a in Assertion.objects:
        count += 1
        print a.arguments
    print count
    
    Assertion.drop_collection()
    
def test_import_traversing():
    Assertion.drop_collection()
    Dataset.drop_collection()
    
    q = MQLQuery.make({'mid':'/m/0p_47'},['*'])
    # 'mid':'/m/0p_47'
    q.get_results('/data/test', 'nholm', 1, None, True, 'mid')
    
    #print 'DONE WITH GET RESULTS'
    for a in Assertion.objects:
        print a.relation
        print a.arguments

    Assertion.drop_collection()
    Dataset.drop_collection()
    
def test_datadumpread(filename):
    
    dump = open(filename, "r")
    count = 0
    for line in dump:
        #print line
        # ADDED: lines 0-200
        
        if count <100:
            print count
            count += 1
            continue
        else:
            print line.split()[0]
            q = MQLQuery.make({'mid':line.split()[0]},['*'])
            q.get_results('/data/freebase', 'nholm', 1, None, True, 'mid')
            count += 1
        
        if count > 200:
            break
    dump.close()


if __name__ ==  "__main__":
    
    conceptdb.connect_to_mongodb('conceptdb')
    
    print len(Assertion.objects)
    prev_len = len(Assertion.objects)
    test_datadumpread("freebase-simple-topic-dump.tsv")

    #test_import_traversing()
    
    print '%d assertions made.'%(len(Assertion.objects)-prev_len)
    #for a in Assertion.objects:
    #    print a.relation
    #    print a.arguments

       