import conceptdb
from conceptdb.freebase_imports import MQLQuery
from conceptdb.assertion import Assertion

def fb_datadumpread(filename):
    
    dump = open(filename, "r")
    count = 0
    for line in dump:
        # ADDED as of 3/8/2011: lines 0-200
        #if count <200:
        #    print count
        #    count += 1
        #    continue
        
        #else:
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
    fb_datadumpread("freebase-simple-topic-dump.tsv")

    
    print '%d assertions made.'%(len(Assertion.objects)-prev_len)

