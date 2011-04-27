import conceptdb
from conceptdb.metadata import Dataset
from conceptdb.assertion import Assertion
from conceptdb.justify import ReasonConjunction
from mongoengine.queryset import QuerySet
from conceptdb.db_merge import *


def test_merge1(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: No assertions
    DB2: Assertions 0-9
    '''
    print "Running test 1: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a1 = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])

    
    testmerge_display(db1, db2)

    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    
    testmerge_check(db1, db2)
    
    print "Finished test 1. "
    
    
def test_merge2(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: No assertions
    DB2: No assertions
    '''
    print "Running test 2: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()

    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()

    
    testmerge_display(db1, db2)
    
    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    
    testmerge_check(db1, db2)
    
    print "Finished test 2."
    
def test_merge3(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: assertions in one dataset
    DB2: assertions in another dataset
    '''
    print "Running test 3: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a = Assertion.make('/data/test1','/rel/IsA',['/test/assertion','test/test%d'%i])
        a.add_support(['/data/test/contributor/nholm'])  

    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a1 = Assertion.make('/data/test2','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])
    
    
    testmerge_display(db1, db2)
    
    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    testmerge_check(db1, db2)
    
    print "Finished test 3."
    
def test_merge4(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: assertions in one dataset
    DB2: assertions in another dataset
    '''
    print "Running test 4: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a = Assertion.make('/data/test1','/rel/IsA',['/test/assertion','test/test%d'%i])
        a.add_support(['/data/test/contributor/nholm'])  

    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a1 = Assertion.make('/data/test2','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])
    
    testmerge_display(db1, db2)
    
    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    testmerge_check(db1, db2)
    
    print "Finished test 4."
    
'''
Creates two test dbs, calls merge
'''
def test_merge5(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: Assertions 0-9
    DB2: Assertions 0-4
    '''
    print "Running test 5: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])
        a.add_support(['/data/test/contributor/nholm'])     

    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(5):
        a1 = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])
        a2 = Assertion.make('/data/test','/rel/HasA',['/test/assertion','test/test%d'%i])  
        a2.add_support(['/data/test/contributor/nholm'])  
        a2.add_support(['/data/test/contributor/nholm1'])
        a2.add_support(['/data/test/contributor/nholm2'])
        a2.add_support(['/data/test/contributor/nholm3'])
        a2.add_support(['/data/test/contributor/nholm4']) 



    testmerge_display(db1, db2)
    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    testmerge_check(db1, db2)
    
    print "Finished test 5."
    
def test_merge6(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: Assertions 0-9
    DB2: Assertions 0-4
    '''
    print "Running test 6: "
    
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])
        a.add_support(['/data/test/contributor/nholm'])    
        a0 = Assertion.make('/data/test1','/rel/IsA',['/test/assertion','test/test%d'%i]) 
        a0.add_support(['/data/test1/contributor/nholm'])    

    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(5):
        a1 = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])
        a2 = Assertion.make('/data/test','/rel/HasA',['/test/assertion','test/test%d'%i])  
        a2.add_support(['/data/test/contributor/nholm'])  
        a3 = Assertion.make('/data/test1','/rel/CausesDesire',['/test/assertion','test/test%d'%i])  
        a3.add_support(['/data/test1/contributor/nholm'])
        
        
    testmerge_display(db1, db2, '/data/test')
    
    '''
    Merge the two dbs
    '''
    merge(db1, db2, '/data/test')
    
    '''
    Check post-merge elements, make sure they match
    '''
    testmerge_check(db1, db2, '/data/test')
    
    print "Finished test 6."

'''
For use with the API:
testmerge_make() just populates two test dbs and gives them reasons
'''
def testmerge_make(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: Assertions 0-9
    DB2: Assertions 0-4
    '''
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    ReasonConjunction.drop_collection()
    for i in xrange(10):
        a = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])
        a.add_support(['/data/test/contributor/nholm'])    
        a0 = Assertion.make('/data/test1','/rel/IsA',['/test/assertion','test/test%d'%i]) 
        a0.add_support(['/data/test1/contributor/nholm'])    

    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    ReasonConjunction.drop_collection()
    for i in xrange(5):
        a1 = Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])  
        a1.add_support(['/data/test/contributor/nholm'])
        a2 = Assertion.make('/data/test','/rel/HasA',['/test/assertion','test/test%d'%i])  
        a2.add_support(['/data/test/contributor/nholm'])  
        a3 = Assertion.make('/data/test1','/rel/CausesDesire',['/test/assertion','test/test%d'%i])  
        a3.add_support(['/data/test1/contributor/nholm'])
        
'''
Displays all of the assertions and reasons currently in each of the two test dbs
'''
def testmerge_display(db1, db2, dataset=None):
    if dataset == None:
        conceptdb.connect_to_mongodb(db1)
        print "Before the merge, db %s has the following assertions: "%db1
        for a1 in Assertion.objects:
            print "assertion: %s"%a1
            print "     confidence score: %s"%a1.confidence
            for r1 in list(ReasonConjunction.objects.filter(target=a1.name)):
                print "     reason: %s"%r1.factors
                assert r1.target == a1.name
    
        conceptdb.connect_to_mongodb(db2)
        print "Before the merge, db %s has the following assertions: "%db2
        for a2 in Assertion.objects:
            print "assertion: %s"%a2
            print "     confidence score: %s"%a2.confidence
            for r2 in list(ReasonConjunction.objects.filter(target=a2.name)):
                print "     reason: %s"%r2.factors
                assert r2.target == a2.name
    else:
        conceptdb.connect_to_mongodb(db1)
        print "Before the merge, db %s has the following assertions: "%db1
        for a1 in Assertion.objects.filter(dataset=dataset):
            print "assertion: %s"%a1
            print "     confidence score: %s"%a1.confidence
            for r1 in list(ReasonConjunction.objects.filter(target=a1.name)):
                print "     reason: %s"%r1.factors
                assert r1.target == a1.name
    
        conceptdb.connect_to_mongodb(db2)
        print "Before the merge, db %s has the following assertions: "%db2
        for a2 in Assertion.objects.filter(dataset=dataset):
            print "assertion: %s"%a2
            print "     confidence score: %s"%a2.confidence
            for r2 in list(ReasonConjunction.objects.filter(target=a2.name)):
                print "     reason: %s"%r2.factors
                assert r2.target == a2.name
            
    
def testmerge_check(db1, db2, dataset=None):
    '''
    Check post-merge elements, make sure they match
    '''
    if dataset==None:
        conceptdb.connect_to_mongodb(db1)
        print "After the merge, db %s has the following assertions: "%db1
        for a1 in Assertion.objects:
            print "assertion: %s"%a1
            print "     confidence score: %s"%a1.confidence
            for r1 in list(ReasonConjunction.objects.filter(target=a1.name)):
                print "     reason: %s"%r1.factors
                assert r1.target == a1.name


        Assertion.drop_collection()
        Dataset.drop_collection()
        ReasonConjunction.drop_collection()
    
        conceptdb.connect_to_mongodb(db2)
        print "After the merge, db %s has the following assertions: "%db2
        for a2 in Assertion.objects:
            print "assertion: %s"%a2
            print "     confidence score: %s"%a2.confidence
            for r2 in list(ReasonConjunction.objects.filter(target=a2.name)):
                print "     reason: %s"%r2.factors
                assert r2.target == a2.name

        Assertion.drop_collection() 
        Dataset.drop_collection()
        ReasonConjunction.drop_collection()
    else:
        conceptdb.connect_to_mongodb(db1)
        print "After the merge, db %s has the following assertions: "%db1
        for a1 in Assertion.objects.filter(dataset=dataset):
            print "assertion: %s"%a1
            print "     confidence score: %s"%a1.confidence
            for r1 in list(ReasonConjunction.objects.filter(target=a1.name)):
                print "     reason: %s"%r1.factors
                assert r1.target == a1.name


        Assertion.drop_collection()
        Dataset.drop_collection()
        ReasonConjunction.drop_collection()
    
        conceptdb.connect_to_mongodb(db2)
        print "After the merge, db %s has the following assertions: "%db2
        for a2 in Assertion.objects.filter(dataset=dataset):
            print "assertion: %s"%a2
            print "     confidence score: %s"%a2.confidence
            for r2 in list(ReasonConjunction.objects.filter(target=a2.name)):
                print "     reason: %s"%r2.factors
                assert r2.target == a2.name

        Assertion.drop_collection() 
        Dataset.drop_collection()
        ReasonConjunction.drop_collection()

    
if __name__=="__main__":
    test_merge1('test1', 'test2')
    test_merge2('test1', 'test2')
    test_merge3('test1', 'test2')
    test_merge4('test1', 'test2')
    test_merge5('test1', 'test2')
    test_merge6('test1', 'test2')
    
    
    