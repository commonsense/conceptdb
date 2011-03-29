import conceptdb
from conceptdb.metadata import Dataset
from conceptdb.assertion import Assertion
from mongoengine.queryset import QuerySet

'''
Given two dbs, merges them
'''
def merge(db1, db2):
    db1_tobeadded = []
    db2_tobeadded = []
    
    conceptdb.connect_to_mongodb(db1)
    db1_assertions = Assertion.objects
    
    conceptdb.connect_to_mongodb(db2)
    db2_assertions = Assertion.objects
    
    for db1_a in [a1 for a1 in list(db1_assertions) if a1 not in list(db2_assertions)]:
        
        db2_tobeadded.append(db1_a)
        
        for db2_check in list(db2_assertions):
            if assertion_check(db1_a, db2_check):
                db2_tobeadded.remove(db1_a)
            
    
    for db2_a in [a2 for a2 in list(db2_assertions) if a2 not in list(db1_assertions)]:
        
        db1_tobeadded.append(db2_a)
        
        for db1_check in list(db1_assertions):
            if assertion_check(db2_a, db1_check):
                db1_tobeadded.remove(db2_a)
    
    conceptdb.connect_to_mongodb(db1)       
    for add1 in db1_tobeadded:
        db1_assertions.create(
                              dataset=db1_assertions[0].dataset,
                              relation=add1.relation,
                              polarity=add1.polarity,
                              argstr=add1.argstr,
                              context=add1.context,
                              complete=1
                              )
    
    conceptdb.connect_to_mongodb(db2)
    for add2 in db2_tobeadded:
        db2_assertions.create(
                              dataset=db2_assertions[0].dataset,
                              relation=add2.relation,
                              polarity=add2.polarity,
                              argstr=add2.argstr,
                              context=add2.context,
                              complete=1
                              )
        
    
    return (db1_assertions, db2_assertions)
        
'''
Two assertion have the same dataset, arguments, relation, polarity, and context
'''                                       
def assertion_check(ass1, ass2):
    if ass1.dataset==ass2.dataset and ass1.argstr==ass2.argstr and ass1.relation==ass2.relation and ass1.polarity==ass2.polarity and ass1.context==ass2.context:
        return True
    return False

'''
Creates two test dbs, calls merge
'''
def test_dbs(db1, db2):
    '''
    Load test assertions into the two DBs:
    DB1: Assertions 0-9
    DB2: Assertions 0-4
    '''
    conceptdb.create_mongodb(db1)
    Assertion.drop_collection()
    Dataset.drop_collection()  
    for i in xrange(10):
        Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])     
    print "Before the merge, db %s has the following assertions: "%db1
    for a1 in Assertion.objects:
        print a1
    
    conceptdb.create_mongodb(db2)
    Assertion.drop_collection()
    Dataset.drop_collection()
    for i in xrange(5):
        Assertion.make('/data/test','/rel/IsA',['/test/assertion','test/test%d'%i])  
        Assertion.make('/data/test','/rel/HasA',['/test/assertion','test/test%d'%i])     
    print "Before the merge, db %s has the following assertions: "%db2
    for a2 in Assertion.objects:
        print a2
    
    '''
    Merge the two dbs
    '''
    merge(db1, db2)
    
    '''
    Check post-merge elements, make sure they match
    '''
    conceptdb.connect_to_mongodb(db1)
    print "After the merge, db %s has the following assertions: "%db1
    for a4 in Assertion.objects:
        print a4 
    Assertion.drop_collection()
    Dataset.drop_collection()
    conceptdb.connect_to_mongodb(db2)
    print "After the merge, db %s has the following assertions: "%db2
    for a3 in Assertion.objects:
        print a3
    Assertion.drop_collection()
    Dataset.drop_collection()
        
    
    
if __name__ == "__main__":
    
    test_dbs('test1', 'test2')
    
    
    