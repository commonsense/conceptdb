import conceptdb
from conceptdb.metadata import Dataset
from conceptdb.assertion import Assertion
from mongoengine.queryset import QuerySet

# Given two querysets, updates them
def merge(db1_assertions, db2_assertions):
    db1_tobeadded = []
    db2_tobeadded = []
    
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
                
    for add1 in db1_tobeadded:
        db1_assertions.create(
                              dataset=db1_assertions[0].dataset,
                              relation=add1.relation,
                              polarity=add1.polarity,
                              argstr=add1.argstr,
                              context=add1.context,
                              complete=1
                              )
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
        
            
# Two assertion have the same arguments, relation, polarity, and context                                  
def assertion_check(ass1, ass2):
    if ass1.argstr==ass2.argstr and ass1.relation==ass2.relation and ass1.polarity==ass2.polarity and ass1.context==ass2.context:
        return True
    return False
        
if __name__ == "__main__":
    
    conceptdb.connect_to_mongodb('test')
    Assertion.drop_collection()
    Dataset.drop_collection()
    
    for i in xrange(10):
        Assertion.make('/data/test1','/rel/IsA',['/test/assertion','test/test%d'%i])
        Assertion.make('/data/test2','/rel/IsA',['/test/assertion','test/test%d'%i])
        
    for j in xrange(10):
        Assertion.make('/data/test1','/rel/HasA',['/test/assertion','test/test%d'%j])
    
    
     # Assertions 0-14, /data/test1 AND /data/test2, AS A QUERYSET
    db1_assertions = Assertion.objects.filter(dataset='/data/test1')
    
    # Assertions 0-9, /data/test1, AS A QUERYSET
    db2_assertions = Assertion.objects.filter(dataset='/data/test2')
    
 
    print 'DB1 before'
    for a1 in db1_assertions:
        print a1
    
    print 'DB2 before'
    for a2 in db2_assertions:
        print a2
    print 'merging....'

    results = merge(db1_assertions, db2_assertions)
    db1_assertions = results[0]
    db2_assertions = results[0]
    
    print 'DB1'
    print type(db1_assertions)
    for db1 in db1_assertions:
        print db1
    
    print 'DB2'
    print type(db2_assertions)
    for db2 in db2_assertions:
        print db2
    
    print 'Assertion.objects'    
    for a in Assertion.objects:
        print a
        
    Assertion.drop_collection()
    Dataset.drop_collection()
    