import mongoengine as mon
from conceptdb.assertion import Assertion
from conceptdb.metadata import Dataset
from mongoengine.queryset import DoesNotExist
from freebase.api.session import MetawebError, HTTPMetawebSession
import freebase
import conceptdb

class MQLQuery():
    
    # mapping of name/values that are being looked for
    query_args = {}
    
    # list of results to pull into assertions
    result_args = []
    
    # list of properties that the importer can probably skip when pulling in properties
    # attribution: where the info in the freebase article comes from
    # creator: freebase user who created the article
    # gumid: URI on the freebase namespace
    # mid: another type of URI
    # permission: read/write permissions for articles
    # key: other names that redirect to a specific freebase article (i.e. Massachusetts Institute of Technology = MIT)
    # search: ???
    # timestamp: when article was last modified
    skip_props = ['attribution', 'creator', 'guid', 'permission', 'search', 'timestamp']
    
    
    def __init__(self, query_args, result_args, skip_props=[]):
        self.query_args = query_args
        self.result_args = result_args
        self.skip_props = self.skip_props+skip_props
                
    
    def fb_entity_from_id(self, dset, user, polarity=1, context=None):
        ''' 
        Called when the result field is '*'
        Returns all of the results (property-value) pairs for the given id object,
        Makes assertions of these results
        '''
        try:
            dataset = Dataset.objects.get(name=dset, language='en')
        except DoesNotExist:
            dataset = Dataset.create(name=dset, language='en')
    
        query = [dict(self.query_args,**{'*':{}})]
        
        assertionscreated = []
        
        # start importing from freebase
        mss = freebase.HTTPMetawebSession("http://api.freebase.com")
        results = mss.mqlread(query)
        #print 'RESULTS ARE'
        #print results
        if type(results)==list:
            results = results[0]
        
        for key in self.query_args.keys():
            initial_assertion = Assertion.make(dataset.name, '/rel/freebase/has%s'%key.capitalize(), [self.query_args['id'],self.query_args[key]])
            initial_assertion.add_support(dataset.name + '/contributor/' + user)
            assertionscreated.append(initial_assertion)
        #print 'MADE INITIAL ASSERTION'
        # Go through all properties, excluding properties in the skip_props list and properties whose results are not of type list  
        for property in [r for r in results if r not in self.skip_props and r not in self.query_args.keys()]:
            # Use properties to index concepts, and only use concepts with an explicit 'mmid' field
            if type(results[property])==list:
                for value in results[property]:
                    try:
                        #print self.query_args['id']
                        #print value['id']
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['id'],value['id']])
                    except:
                        #print self.query_args['id']
                        #print value['id']
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['id'],value['value']])
                
                    a.add_support(dataset.name + '/contributor/' + user)
                    assertionscreated.append(a)
            else:
                #print results[property]
                try:
                    a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['id'],results[property]['value']])
                    a.add_support(dataset.name + '/contributor/' + 'nholm')
                    assertionscreated.append(a)
                except:
                    #print 'second exception'
                    #a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mmid'],results[property]['mmid']])
                    try:
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['id'],results[property]['id']])
                        a.add_support(dataset.name + '/contributor/' + 'nholm')
                        assertionscreated.append(a)
                    except:
                        pass
            
        return assertionscreated
    
    def fb_entity_property_from_id(self, dset, user, polarity=1, context=None):
        '''
        Called when the result field is not '*',
        Only returns (property,value) pairs for properties 
        listed in the results_args and query_args,
        Makes assertions for all of these pairs
        '''
        # create or get dataset
        try:
            dataset = Dataset.objects.get(name=dset, language='en')
        except DoesNotExist:
            dataset = Dataset.create(name=dset, language='en')
        
        query = [self.query_args]
        
        assertionscreated = []
        
        # start importing from freebase
        mss = HTTPMetawebSession("http://api.freebase.com")
        
        for searchterm in self.result_args:
            query[0][searchterm]={}
            try:    
                results = mss.mqlread(query)
                a = Assertion.make(dataset.name, '/rel/freebase/has%s'%searchterm.capitalize(), [self.query_args['id'],results[0][searchterm]['id']])
                a.add_support(dataset.name + '/contributor/' + user)           
                assertionscreated.append(a)
        
            except MetawebError as me1:
                if str(me1.args).rfind('/api/status/error/mql/result') is not -1:
                    query[0][searchterm]=[{}]
                    results = mss.mqlread(query)
                    for result in results[0][searchterm]:
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%searchterm.capitalize(), [self.query_args['id'],result['id']])
                        a.add_support(dataset.name + '/contributor/' + user)
                        assertionscreated.append(a)
                
                elif str(me1.args).rfind('/api/status/error/mql/type') is not -1:
                    print 'The property %s is not recognized.' % searchterm
                    return
            
                else:
                    print str(me1.args)
                    return
        
            del query[0][searchterm]
        return assertionscreated
    
    def fb_all_from_id(self, dset, user, polarity=1, context=None):
        '''
        Called when the import should go several layers, 
        i.e. all of the properties, and all of the values of all of the properties, etc
        '''
        
        query = [self.query_args]
        
        assertionscreated = []
        
        if 'type' in self.query_args.keys():
            pass
        else:
            # start with all of the immediate properties of the mmid
            assertionscreated = self.fb_entity_from_id(dset, user, polarity, context)
            
            # add all of the properties including possible other query values
            for property in MQLQuery.view_props(self.query_args):
                if property == 'type':
                    #print 'in property = type'
                    for value in MQLQuery.view_entities(self.query_args, property):
                       # print 'AT VALUE: %s'%value
                        query[0][property] = value
                        for assertion in self.fb_entity_from_id(dset, user, polarity, context):
                            #print 'ADDING ASSERTION WITH ARGS %s, %s'%(assertion.arguments, assertion.relation)
                            assertionscreated.append(assertion)
                            
                        del query[0][property]
                else:
                    # TODO: figure out what to do for other queries, that have multiple results
                    # but no specific result term
                    pass 
        
        return assertionscreated
    
    def fb_entity_from_mid(self, dset, user, polarity=1, context=None):
        ''' 
        Called when the result field is '*'
        Returns all of the results (property-value) pairs for the given mid object,
        Makes assertions of these results
        '''
        try:
            dataset = Dataset.objects.get(name=dset, language='en')
        except DoesNotExist:
            dataset = Dataset.create(name=dset, language='en')
    
        query = [dict(self.query_args,**{'*':{}})]
        
        assertionscreated = []
        
        # start importing from freebase
        mss = freebase.HTTPMetawebSession("http://api.freebase.com")
        try:
            results = mss.mqlread(query)
        except MetawebError:
            print 'MetawebError occurred at %s'%str(query)
            return []
        
        
        #print results[0]
        
        if type(results)==list:
            results = results[0]
        
        #for key in self.query_args.keys():
        #    initial_assertion = Assertion.make(dataset.name, '/rel/freebase/has%s'%key.capitalize(), [self.query_args['mid'],self.query_args[key]])
        #    initial_assertion.add_support(dataset.name + '/contributor/' + user)
        #    assertionscreated.append(initial_assertion)
        
        for property in [r for r in results if r not in self.skip_props and r not in self.query_args.keys()]:
            #print property
            
            if type(results[property])==list:
                for value in results[property]:
                    try:
                        #print self.query_args['id']
                        #print value['id']
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mid'],value['id']])
                    except:
                        #print self.query_args['id']
                        #print value['id']
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mid'],value['value']])
                
                    a.add_support(dataset.name + '/contributor/' + user)
                    assertionscreated.append(a)
            else:
                #print results[property]
                try:
                    a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mid'],results[property]['value']])
                    a.add_support(dataset.name + '/contributor/' + 'nholm')
                    assertionscreated.append(a)
                except:
                    #print 'second exception'
                    #a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mmid'],results[property]['mmid']])
                    try:
                        a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [self.query_args['mid'],results[property]['id']])
                        a.add_support(dataset.name + '/contributor/' + 'nholm')
                        assertionscreated.append(a)
                    except:
                        pass
        return assertionscreated
    
    def fb_all_from_mid(self, dset, user, polarity=1, context=None):
        '''
        Called when the import should go several layers, 
        i.e. all of the properties, and all of the values of all of the properties, etc
        '''
        
        query = [self.query_args]
        
        assertionscreated = []
        
        if 'type' in self.query_args.keys():
            pass
        else:
            # start with all of the immediate properties of the mmid
            assertionscreated = self.fb_entity_from_mid(dset, user, polarity, context)
            
            # add all of the properties including possible other query values
            for property in MQLQuery.view_props(self.query_args):
                if property == 'type':
                    #print 'in property = type'
                    #print 'ENTITIES ARE:'
                    #print MQLQuery.view_entities(self.query_args, property)
                    for value in MQLQuery.view_entities(self.query_args, property):
                       # print 'AT VALUE: %s'%value
                        #print 'VALUE IS'+value
                        #print 'PROPERTY IS'+property
                        query[0][property] = value
                        for assertion in self.fb_entity_from_mid(dset, user, polarity, context):
                            #print 'ADDING ASSERTION WITH ARGS %s, %s'%(assertion.arguments, assertion.relation)
                            assertionscreated.append(assertion)
                            
                        del query[0][property]
                else:
                    # TODO: figure out what to do for other queries, that have multiple results
                    # but no specific result term
                    pass 
        
        return assertionscreated
        

      
    def check_arguments(self):
        '''
        Very simple argument checks before fb_entity, fb_entity_property, fb_all
        can be called
        Check 1: '*' has to be an exclusive result_args item, if it is one
        Check 2: 'id' should always be in query_args
        '''
        if '*' in self.result_args: 
            # '*' should be the ONLY result arg
            if len(self.result_args)!=1:
                print 'Can only have one * argument'
                return False

        return ('id' in self.query_args.keys() or 'mid' in self.query_args.keys())
            
                
    
    @staticmethod
    def make(query_args, result_args):
        '''
        Constructs MQLQuery instance
        '''
        mqlquery = MQLQuery(query_args, result_args)
        
        return mqlquery
    
    
    def get_results(self, dataset, user, polarity=1, context=None, import_all=False, id_type='id'):
        '''
        Depending on whether the importing should be single-level and what the result
        args are, calls the fb_ importing methods
        '''
        # verify that query doesn't have errors with specific results
        if self.check_arguments() == False:
            print 'Arguments: %s were not compatible with query type: %s .'%(str(self.query_args),str(self.result_args))
            return
        
        if id_type=='id':
            if import_all:
                return self.fb_all_from_id(dataset, user, polarity, context)
            else:
                if self.result_args==['*']:
                    return self.fb_entity_from_id(dataset, user, polarity, context)
                else:
                    return self.fb_entity_property_from_id(dataset, user, polarity, context)
        elif id_type=='mid':
            if import_all:
                return self.fb_all_from_mid(dataset, user, polarity, context)
            else:
                if self.result_args==['*']:
                    return self.fb_entity_from_mid(dataset, user, polarity, context)
                else:
                    return self.fb_entity_property_from_mid(dataset, user, polarity, context)
            
            
    @staticmethod
    def connect_to_sentence(assertion):
        '''
        Omitted from the code for now, can be used to make expressions and
        sentences connect to corresponding assertions;
        relation=  [relationmmid,relationname] (i.e. ['/rel/freebase/album, "has album"]),
        concepts= [conceptmmid, conceptname] (i.e. ['/en/the_beatles', 'The Beatles'])
        '''
        e = assertion.make_expression('{0} has %s {1}'%property, assertion.arguments, 'en')                  
        assertion.connect_to_sentence(assertion.dataset, '%s %s %s.'%(assertion.arguments[0],assertion.relation,assertion.arguments[1]))
        
        return assertion
    
    @staticmethod
    def view_props(query_args):
        '''
        Called with a specific query to check; 
        simply returns the possible properties generated by that query
        '''
        query = [dict(query_args,**{'*':{}})]
        
        props = []
        
        mss = freebase.HTTPMetawebSession("http://api.freebase.com")
        results = mss.mqlread(query)
        for r in results[0]:
            if r not in MQLQuery.skip_props:
                props.append(r)
        
        return props
    
    
    @staticmethod
    def view_entities(query_args, property):
        '''
        Called with a specific query and a property to check;
        returns all of the possible values of the specified property
        '''
        query = [dict(query_args,**{property:None})]
        
        entities = []
    
        mss = freebase.HTTPMetawebSession("http://api.freebase.com")
        try:
            results = mss.mqlread(query)
            #print 'results0propertyis'
            #print results[0][property]
            entities.append(results[0][property])
        except MetawebError:
            query[0][property]=[]
            results = mss.mqlread(query)
            for r in results[0][property]:
                entities.append(r)
        except:
            print 'Property %s is not recognized.'%property
            return
        
        return entities
    