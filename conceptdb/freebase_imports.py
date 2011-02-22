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
    
    # mapping of name/parameters that should be returned 
    # key possibilities: any of the properties that will be returned by the type, or '*' for all properties
    # value possibilities: [] for values of property mappings, {} for all properties of property mappings, None for single value
    result_args = []
    
    # to be submitted to the mqlread command
    #query = {}
    
    # list of properties in every freebase object
    skip_props = ['attribution', 'creator', 'guid', 'mid', 'permission', 'key', 'search', 'timestamp']
    
    
    def __init__(self, query_args, result_args, skip_props=[]):
        self.query_args = query_args
        self.result_args = result_args
#        self.query = dict(query_args, **self.result_args)
        self.skip_props = self.skip_props+skip_props
    
    # Method for making an assertion, expression, and sentence; given a dataset object,
    # relation object of type [relationid,relationname] (i.e. ['/rel/freebase/album, "has album"]
    # concepts object of type 
    @staticmethod
    def connect_to_sentence(dataset, relation, concepts, user, polarity=1, context=None):
        
        try:
            a = Assertion.objects.get(
                dataset=dataset.name,
                relation=relation[0],
                polarity=polarity,
                argstr=Assertion.make_arg_string([concepts[0][0],concepts[1][0]]),
                context=context
                )
            
#            a.add_support(dataset.name + '/contributor/' + user)
                    
        except DoesNotExist:
                    
            a = Assertion.make(dataset.name, relation[0], [concepts[0][0],concepts[1][0]])
            e = a.make_expression('{0} has %s {1}'%property, a.arguments, 'en')                  
            a.connect_to_sentence(dataset, '%s %s %s.'%(concepts[0][1],relation[1],concepts[1][1]))
            
#            a.add_support(dataset.name + '/contributor/' + user)
        
        return a
    
#    Using query_args, returns a list of properties that can be entered into result_args
    @staticmethod
    def view_props(query_args):
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
        query = [dict(query_args,**{property:None})]
        
        entities = []
    
        mss = freebase.HTTPMetawebSession("http://api.freebase.com")
        try:
            results = mss.mqlread(query)
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
                
    
    # Called when the result field is simply '*'; returns and adds all fields associated with query
    def fb_entity(self, dset, user, polarity=1, context=None):
        ''' 
        Called when the result field is '*'
        '''
        
        # create or get dataset
        try:
            dataset = Dataset.objects.get(name=dset, language='en')
        except DoesNotExist:
            dataset = Dataset.create(name=dset, language='en')
        
        query = [dict(self.query_args,**{'*':{}})]
        
        # start importing from freebase
        mss = HTTPMetawebSession("http://api.freebase.com")
        results = mss.mqlread(query)
        if type(results)==list:
            results = results[0]
            
        
        returnlist = []
        
        # Go through all properties, excluding properties in the skip_props list and properties whose results are not of type list  
        for property in [r for r in results if r not in self.skip_props and type(results[r])==list]:
            # Use properties to index concepts, and only use concepts with an explicit 'id' field
            for concept in [conc for conc in results[property] if 'id' in conc.keys()]:
                        
                try:
                    a = Assertion.objects.get(
                        dataset=dataset.name,
                        relation='/rel/freebase/has%s'%property.capitalize(),
                        polarity=polarity,
                        argstr=Assertion.make_arg_string([results['id'],concept['id']]),
                        context=context
                        )
            
                    a.add_support(dataset.name + '/contributor/' + user)
                    
                except DoesNotExist:
                    
                    a = Assertion.make(dataset.name, '/rel/freebase/has%s'%property.capitalize(), [results['id'],concept['id']])
                            
                            
                returnlist.append(a.serialize())
        
        return returnlist
    
    # Called when results 
    def fb_entity_property(self, dset, polarity, context, user):
        '''
        Called when the result field is not '*'
        '''
        # create or get dataset
        try:
            dataset = Dataset.objects.get(name=dset, language='en')
        except DoesNotExist:
            dataset = Dataset.create(name=dset, language='en')
        
        query = [self.query_args]
        
        returnlist = []
        
        # start importing from freebase
        mss = HTTPMetawebSession("http://api.freebase.com")
        
        for searchterm in self.result_args:
            query[0][searchterm]={}
            try:    
                results = mss.mqlread(query)
     
                try:
                    a = Assertion.objects.get(
                        dataset=dataset.name,
                        relation='/rel/freebase/has%s'%searchterm.capitalize(),
                        polarity=polarity,
                        argstr=Assertion.make_arg_string([self.query_args['id'],results[0][searchterm]['id']]),
                        context=context
                        )
            
                    a.add_support(dataset.name + '/contributor/' + user)
                    
                except DoesNotExist:
                    
                    a = Assertion.make(dataset.name, '/rel/freebase/has%s'%searchterm.capitalize(), [self.query_args['id'],results[0][searchterm]['id']])
                    
                    a.add_support(dataset.name + '/contributor/' + user)
                    
                returnlist.append(a.serialize())
        
            except MetawebError as me1:
                if str(me1.args).rfind('/api/status/error/mql/result') is not -1:
                    query[0][searchterm]=[{}]
                    results = mss.mqlread(query)
                    for result in results[0][searchterm]:
                                           
                        try:
                            a = Assertion.objects.get(
                                dataset=dataset.name,
                                relation='/rel/freebase/has%s'%searchterm.capitalize(),
                                polarity=polarity,
                                argstr=Assertion.make_arg_string([self.query_args['id'],result['id']]),
                                context=context
                                )
            
                            a.add_support(dataset.name + '/contributor/' + user)
                    
                        except DoesNotExist:
                    
                            a = Assertion.make(dataset.name, '/rel/freebase/has%s'%searchterm.capitalize(), [self.query_args['id'],result['id']])
                    
                            a.add_support(dataset.name + '/contributor/' + user)
                            
                        returnlist.append(a.serialize())
                
                elif str(me1.args).rfind('/api/status/error/mql/type') is not -1:
                    print 'The property %s is not recognized.' % searchterm
                    return
            
                else:
                    print str(me1.args)
                    return
        
            del query[0][searchterm]
        return returnlist
    
    def fb_all(self, dset, polarity, context, user):
            # create or get dataset
        
        query = [self.query_args]
        
        returnlist = []
        
        if 'type' in self.query_args.keys():
            pass
        else:
            # start with all of the immediate properties of the id
            returnlist = self.fb_entity(dset, user, polarity, context)
            
            # add all of the properties including possible other query values
            for property in MQLQuery.view_props(self.query_args):
                if property == 'type':
                    for value in MQLQuery.view_entities(self.query_args, property):
                        query[0][property] = value
                        print 'QUERY IS '+str(query)
                        for a in self.fb_entity(dset, polarity, context, user):
                            returnlist.append(a)
                    
                        del query[0][property]
                else:
                    # TODO: figure out what to do for other queries, that have multiple results
                    # but no specific result term
                    pass 
        
        return returnlist

      
    def check_arguments(self):
        #superficial check, doesn't check for metaweb errors
        
        # make sure result arguments are separate from query arguments!
        if '*' in self.result_args: 
            # '*' should be the ONLY result arg
            if len(self.result_args)!=1:
                print 'Can only have one * argument'
                return False

        return ('id' in self.query_args.keys())
            
                
    
    @staticmethod
    def make(query_args, result_args):
        
        # Construct instance of MQLQuery
        mqlquery = MQLQuery(query_args, result_args)
        
        return mqlquery
    
    
    def get_results(self, dataset, polarity=1, context=None, user=None, import_all=False):
        
        # verify that query doesn't have errors with specific type
        if self.check_arguments() == False:
            print 'Arguments: '+str(self.query_args)+ ' were not compatible with query type: '+self.query_type
            return
        
        if import_all:
            return self.fb_all(dataset, polarity, context, user)
        else:
            if self.result_args==['*']:
                return self.fb_entity(dataset, polarity, context, user)
            else:
                return self.fb_entity_property(dataset, polarity, context, user)
    