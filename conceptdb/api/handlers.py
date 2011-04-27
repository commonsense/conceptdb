from piston.handler import BaseHandler
from piston.utils import throttle, rc
from piston.authentication import HttpBasicAuthentication
from conceptdb.assertion import Assertion, Sentence, Expression
from conceptdb.metadata import Dataset
from conceptdb.justify import ReasonConjunction
from conceptdb.freebase_imports import MQLQuery
from conceptdb import ConceptDBDocument
from conceptdb.db_merge import merge
import conceptdb
from mongoengine.queryset import DoesNotExist
from mongoengine.base import ValidationError
from csc.conceptnet.models import User

basic_auth = HttpBasicAuthentication()

conceptdb.connect_to_mongodb('test') #NOTE: change when not testing

class ConceptDBHandler(BaseHandler):
    """The ConceptDBHandler deals with all accesses to the conceptdb 
    from the api.  A GET to it can return a dataset, assertion, or reason. 
    Searching for a concept will return the top ranked assertions that the 
    concept is part of.  
    A POST to it can create an assertion or vote on one."""

    allowed_methods = ('GET','POST')

    @throttle(600,60,'read')
    def read(self, request, obj_url):
        obj_url = '/'+obj_url
        if obj_url.startswith('/data'):#try to find matching dataset
            return self.datasetLookup(obj_url)
        elif obj_url.startswith('/assertion/'):
            #matches /assertion/id, look up by id
            return self.assertionLookup(obj_url)
        elif obj_url.startswith('/assertionfind'):
            #find assertion by identifying factors (dataset, concepts, relation, polarity, context)
            return self.assertionFind(request, obj_url)
        elif obj_url.startswith('/factorusedfor'):
            #returns all of the things that a reason has been used to justify
            return self.factorUsedFor(obj_url)
        elif obj_url.startswith('/reason'):
            #looks up a reason by its name
            return self.reasonLookup(obj_url)
        elif obj_url.startswith('/conceptfind'):
            #returns assertions that a concept has appeared in (as a concept, not relation or context)
            #defaults to returning top 10 by justification but can be modified
            return self.conceptLookup(request, obj_url)
        elif obj_url.startswith('/expression'):
            return self.expressionLookup(obj_url)
        elif obj_url.startswith('/assertionexpressions'):
            return self.assertionExpressionLookup(request, obj_url)
        elif obj_url.startswith('/freebaselookupprops'):
            return self.freebaseLookupProps(request, obj_url)
        elif obj_url.startswith('/freebaselookupentities'):
            return self.freebaseLookupEntities(request, obj_url)
        #if none of the above, return bad request.  
        return rc.BAD_REQUEST

    @throttle(200,60,'update')
    def create(self, request, obj_url):
        ''
        #can start with /assertionmake, /assertionvote, /freebaseimport.  
        
        obj_url = '/' + obj_url
        
        #If assertionmake,looks for the assertion.  If can't find, makes 
        #it and contributes a positive vote.  If it can find it, contribute 
        #a positive vote and inform the user.
        if obj_url.startswith('/assertionmake'):
            return self.assertionMake(request, obj_url)
        
        #If assertionvote, looks for the assertion and votes on it.  If it can't find
        #it nothing happens.
        elif obj_url.startswith('/assertionvote') or obj_url.startswith('/assertionidvote'):
            return self.assertionVote(request, obj_url)
        
        #If freebaseimport, queries freebase for entities to be added. If it 
        #finds entities, adds the entire array of entities. If the query returns None,
        #nothing happens. If the entity to be added exists in assertion objects, 
        #contribute a positive vote and inform the user.
        elif obj_url.startswith('/freebaseimport'):
            return self.freebaseImport(request, obj_url)
        
        #If freebasefullimport, does queries freebase with all of the possible types, and 
        # imports them all
        elif obj_url.startswith('/freebasefullimport'):
            return self.freebaseFullImport(request, obj_url)
        
        elif obj_url.startswith('/dbmerge'):
            return self.db_merge(request, obj_url)
        
        # else return bad request
        return rc.BAD_REQUEST

    def datasetLookup(self,obj_url):
        """Method called when going to /api/data/{dataset name}.  Returns 
        a serialized version of the dataset."""

        try:
            return Dataset.get(obj_url).serialize()
        except DoesNotExist:
            return rc.NOT_FOUND

    def assertionLookup(self, obj_url):
        """Method called to look up an assertion by its id number.  Accessed
        by going to URL /api/assertion/{id}.  Returns a serialized version 
        of the assertion."""
        try:
            return Assertion.get(obj_url.replace('/assertion/', '')).serialize()    
        except DoesNotExist:
            return rc.NOT_FOUND
        except ValidationError: #raised if input is not a valid id
            return rc.NOT_FOUND

    def assertionFind(self, request, obj_url):
        """Method called to look up an assertion by its attributes, when the id 
        number is not known.  Accessed by going to URL /api/assertionfind.  Must
        include parameters for the dataset, relation, concepts, polarity, and context.  

        /api/assertionfind?dataset={datasetname}&rel={relation}&concepts={concept1,concept2,etc}
        &polarity={polarity}&context={context}

        Polarity and context are optional parameters, defaulting to polarity = 1 and context = None
        """

        dataset = request.GET['dataset']
        relation = request.GET['rel']
        argstr = request.GET['concepts']
        polarity = float(request.GET.get('polarity',1))
        context = request.GET.get('context','None')
        
        if context == 'None':
            context = None

        try:
            return Assertion.objects.get(
                dataset = dataset,
                relation = relation,
                argstr = argstr,
                polarity = polarity,
                context = context).serialize()
        except DoesNotExist:
            return rc.NOT_FOUND


    def factorUsedFor(self, obj_url):
        """Given a factor in a ReasonConjunction object, returns all of the things
        that the reason has been used to justify. Currently returns a list of the things
        that use it in form {assertions: [list of assertions], sentence: [list of sentences],
        expression: [list of expressions]}.  If the reason has also been used to 
        justify things that are not in the database (for instance Users), it will
        inform you but not return the other items.  I might change this later.  
        
        URL must take the form /api/factorusedfor/{reason id}"""

        #must look for the reason being used in Assertion, Sentence, and Expression
        #TODO: should there be a limit on the number of things returned,  maybe also
        #sorted by confidence scores?  
        
        factorName = obj_url.replace('/factorusedfor', '')
        assertions = [] #list of assertion id's with obj_url as justification
        expressions = [] #list of expressions with obj_url as justification
        sentences = [] #list of sentences with obj_url as justification
        other = False #
        cursor = ReasonConjunction.objects._collection.find({'factors':factorName})
        while(True):
            try:
                next_item = cursor.next()['target']
                
                #if target was the document itself, change to document name
                if isinstance(next_item, ConceptDBDocument):
                    next_item = next_item.name

                if isinstance(next_item, basestring) == False:
                    #not a ConceptDBDocument.
                    other = True
                    continue;

                #go through and add assertion ids to assertion list,
                #expression ids to expression list,
                #sentence ids to sentence list.  
                if next_item.startswith('/assertion'):
                    assertions.append(next_item.replace('/assertion/', ''))
                elif next_item.startswith('/expression'):
                    expressions.append(next_item.replace('/expression/', ''))
                elif next_item.startswith('/sentence/'):
                    sentences.append(next_item.replace('/sentence/', ''))
                else: #not a database item
                    other = True
            except StopIteration:
                break


        if (len(sentences) == len(assertions) == len(expressions) == 0) and (other == False):
            #not used to justify anything
            return rc.NOT_FOUND

        ret = "{'assertions':" + str(assertions) + ", 'sentences':" + str(sentences) + ", 'expressions':" + str(expressions) + "}"

        if other:
            ret = ret + "\nThis reason is also used to justify non-database items."
        
        return ret 

    def reasonLookup(self, obj_url):
        """Method allows you to look up a ReasonConjunction by its id.  
        Accessed by going to URL /api/reason/{id}
        """
        try:
            return ReasonConjunction.objects.get(obj_url.replace('/reason/', '')).serialize()
        except DoesNotExist:
            return rc.NOT_FOUND

    def conceptLookup(self, request, obj_url):
        """
        Method looks up the assertions that the concept participates in (as an argument,
        not as a relation or a context).  From a list of concept assertions ranked by
        confidence score, it returns the assertions from rank start:start+limit, in the 
        form of a list.  Defaults start = 0, limit = 10.  If there are fewer assertions
        containing the concept than start + limit, it cuts off at the last one.  

        Accessed by going to URL /api/concept/{name}?start={x}&limit={y}
        """

        #TODO: implement ranking by confidence score
        #TODO: maybe remember state so can implement paging

        start = int(request.GET.get('start', '0'))
        limit = int(request.GET.get('limit', '10'))
        conceptName = obj_url.replace('/conceptfind', '')
        #NOTE: should return ranked by confidence score.  For now assume that they do.
        cursor = Assertion.objects._collection.find({'arguments':conceptName})[start:start + limit]
        assertions = []


        while (True):
            try:
                assertions.append(str(cursor.next()['_id']))
            except StopIteration:
                break #no more assertions within the skip/limit boundaries

        if len(assertions) == 0: #no assertions were found for the concept
            return rc.NOT_FOUND

        return "{assertions: " + str(assertions) + "}"

    def assertionMake(self, request, obj_url):
        """This method takes the unique identifiers of an assertion as its arguments:
        dataset, relation, concepts, context, and polarity.  It checks to see if this
        assertion exists.  If it does not, it creates it and adds the submitting user's
        vote as a justification.  If it exists already, it adds the submitting user's
        vote as a justification.

        Accessed by going to the URL
        /api/assertionmake?dataset={dataset}&rel={relation}&concepts={concept1,concept2,etc}&
        polarity={polarity}&context={context}&user={username}&password={password}

        Polarity and context are optional, defaulting to polarity = 1 context = None
        """
        dataset = request.POST['dataset']
        relation = request.POST['rel']
        argstr = request.POST['concepts']
        arguments = argstr.split(',')
        polarity = int(request.POST.get('polarity','1'))
        context = request.POST.get('context','None')
        user = request.POST['user']
        password = request.POST['password']

        if context == "None":
            context = None
        # TODO: uncomment to take into account user and password?
        if User.objects.get(username=user).check_password(password):
            #the user's password is correct.  Get their reason and add
            
            try:
                user_reason = ReasonConjunction.objects.get(target=dataset + '/contributor/' + user)
            except DoesNotExist:
                return rc.FORBIDDEN
        else:
            #incorrect password
            return rc.FORBIDDEN
        
        try:
            assertion = Assertion.objects.get(
                dataset = dataset,
                relation = relation,
                argstr = argstr,
                polarity = polarity,
                context = context)
            
            assertion.add_support([dataset + '/contributor/' + user]) 
            return "The assertion you created already exists.  Your vote for this \
            assertion has been counted.\n" + str(assertion.serialize())

        except DoesNotExist:
            assertion = Assertion.make(dataset = dataset,
                        arguments = arguments,
                        relation = relation,
                        polarity = polarity,
                        context = context)
            
            assertion.add_support([dataset + '/contributor/' + user]) 

            return assertion.serialize()


    def assertionVote(self, request, obj_url):
        """Assertion vote is called whenever someone is voting on an assertion.  It can 
        be accessed in one of 2 ways: voting on an assertion identified directly by its id
        or voting on an assertion identified by its unique attributes. To add a positive vote,
        the user should make vote=1.  A negative vote is vote=-1.  Any other values will result
        in no action being taken.  

        Can be accessed through either of the following URLS:
        /api/assertionvote?dataset={dataset}&rel={relation}&concept={concept1,concept2,etc}
        &polarity={polarity}&context={context}&vote={vote}&user={username}&password={password}

        polarity and context are optional values, defaulting to polarity = 1 and context = None

        /api/assertionidvote?id={id}&vote={vote}
        """
        
        user = request.POST['user']
        password = request.POST['password']
        
         
        if obj_url.startswith('/assertionvote'):
            dataset = request.POST['dataset']
            relation = request.POST['rel']
            argstr = request.POST['concepts']
            polarity = int(request.POST.get('polarity','1'))
            context = request.POST.get('context','None')

            if context == "None":
                context = None

            
            try:
                 assertion = Assertion.objects.get(
                     dataset = dataset,
                     relation = relation,
                     argstr = argstr,
                     polarity = polarity,
                     context = context)
            except DoesNotExist:
                return rc.NOT_FOUND
        else:
            id = request.POST['id']

            try:
                assertion = Assertion.get(id)
                dataset = assertion.dataset
            except DoesNotExist:
                return rc.NOT_FOUND
        
        if User.objects.get(username=user).check_password(password):

            #the user's password is correct.  Get their reason and add
            try:
              ReasonConjunction.objects.get(target = dataset + '/contributor/' + user)
            except DoesNotExist:
              return rc.FORBIDDEN
        else:
            #incorrect password
            return rc.FORBIDDEN
         
        vote = request.POST['vote']
        if vote == "1": #vote in favor
            assertion.add_support([dataset + '/contributor/' + user]) 
        elif vote == "-1": #vote against
            assertion.add_oppose([dataset + '/contributor/' + user])
        else: #invalid vote
            return rc.BAD_REQUEST

        return assertion.serialize()


    def expressionLookup(self, obj_url):
        try:
            return Expression.get(obj_url.replace('/expression/', ''))
        except DoesNotExist:
            return rc.NOT_FOUND

# expression lookup where given an assertion, while return given number of 
#expressions that match the assertion -- similar to how concept lookup works now?
    def assertionExpressionLookup(self, request, obj_url):
        assertionID = request.GET['id']
        start = int(request.GET.get('start', '0'))
        limit = int(request.GET.get('limit', '10'))

        #NOTE: should return ranked by confidence score.  For now assume that they do.
        try:
            assertion = Assertion.get(assertionID)
        except DoesNotExist:
            return rc.NOT_FOUND
        cursor = Expression.objects(assertion = assertion)[start:start + limit]
        expressions = []
        while (True):
            try:
                expressions.append(str(cursor.next().id))
            except StopIteration:
                break #no more assertions within the skip/limit boundaries

        if len(expressions) == 0: #no assertions were found for the concept
            return rc.NOT_FOUND

        return "{expressions: " + str(expressions) + "}"
    
    def freebaseImport(self, request, obj_url):
        #TODO: import a freebase entity with MQL query, given id
        """
        Imports only one layer deep (i.e. all of the types associated with id, 
        or all of the properties of an id with a given type
        
        This method takes a json object or dictionary of query arguments, which 
        may include id, type, guid, mid, timestamp, name, or any keyword found 
        in the freebase schema. Using another json object to represent what to look 
        for in the results (specific keywords representing certain field, or '*' representing 
        all fields), does an MQL query, makes all results into assertions, and returns
        the result set. 
        query_args: id:someid,type:sometype...
        result_args: name:somename,*:{}
        
        Accessed by going to the URL
        /api/assertionmake?dataset={dataset}&query_args={arg1:val1,arg2:val2,...}&result_args=
        {arg1,arg2,arg3,...}&polarity={polarity}&context={context}&user={user}&password={password}
        
        TODO: maybe include details about keywords, details about result_args field
        
        tested:
        curl --data "dataset=/data/test&args=id:/en/the_beatles&results=*&polarity=1&context=None&user=nholm&password=something" "http://127.0.0.1:8000/api/freebaseimport"
        """
        
        dataset = request.POST['dataset']
        
        query_args_str = request.POST['args']
        query_args={}
        for arg in query_args_str.split(','):
            query_args[arg.split(':')[0]]=arg.split(':')[1]

        result_args_str = request.POST['results']
        result_args = result_args_str.split(',')
        
            
        polarity = int(request.POST.get('polarity','1'))
        context = request.POST.get('context','None')
        user = request.POST['user']
        password = request.POST['password']

        if context == "None":
            context = None
            
        if User.objects.get(username=user).check_password(password):
            #the user's password is correct.  Get their reason and add
            try:
                user_reason = ReasonConjunction.objects.get(target=dataset + '/contributor/' + user)
            except DoesNotExist:
                return rc.FORBIDDEN
        else:
            #incorrect password
            return rc.FORBIDDEN
        
        mqlquery = MQLQuery.make(query_args, result_args)
        
        assertions_from_freebase = mqlquery.get_results(dataset, user, polarity, context, False)
        
#        return '{imported assertions: '+str(assertions_from_freebase)+'}'
        return '{Added/voted for %s assertions from freebase for %s}'%(str(len(assertions_from_freebase)),str(query_args))

    
    def freebaseLookupProps(self, request, obj_url):
        '''
        Given a fb query, looks up all of the properties associated with that object. 
        These properties can become result_args fields.
        
        Format: /api/freebaselookupprops?args={arg1:val1,arg2:val1,...}
        
        tested:
        curl "http://127.0.0.1:8000/api/freebaselookupprops?args=id:/en/the_beatles"
        curl "http://127.0.0.1:8000/api/freebaselookupprops?args=id:/en/the_beatles,type:/music/artist"
        
        '''
        
        query_args={}
        query_args_str = request.GET['args']
        for a in query_args_str.split(','):
            query_args[a.split(':')[0]]=a.split(':')[1]
        
        return '{ The result set has the following properties: '+str(MQLQuery.view_props(query_args))+'}'

    def freebaseLookupEntities(self, request, obj_url):
        '''
        Given a fb query, and a property, looks up all of the possible values that can 
        be inserted for that property, i.e. type='/common/topic','/music/artist', ...
        
        Format: /api/freebaselookupentities?args={arg1:val1,arg2:val1,...}&property={prop}
        
        tested:
        curl "http://127.0.0.1:8000/api/freebaselookupentities?args=id:/en/the_beatles&property=type"
        '''
        
        query_args={}
        query_args_str = request.GET['args']
        for a in query_args_str.split(','):
            query_args[a.split(':')[0]]=a.split(':')[1]
        
        property = request.GET['property']
        
        return '{ The property %s can be assigned the following entities: %s}'%(property,str(MQLQuery.view_entities(query_args, property)))
    
    def freebaseFullImport(self, request, obj_url):
        '''
        Import ALL URIs associated with a given freebase URI
        freebase URI field : 'id'
        
        Basic operation: if only id given, does a separate import for all of the 
        properties of each possible type. if type given, only do an import for that layer.
        if other property given, do that same query with every possible type
        '''
        dataset = request.POST['dataset']
        
        query_args_str = request.POST['args']
        query_args={}
        for arg in query_args_str.split(','):
            query_args[arg.split(':')[0]]=arg.split(':')[1]

        result_args_str = request.POST['results']
        result_args = result_args_str.split(',')
        
            
        polarity = int(request.POST.get('polarity','1'))
        context = request.POST.get('context','None')
        user = request.POST['user']
        password = request.POST['password']

        if context == "None":
            context = None
            
        if User.objects.get(username=user).check_password(password):
            #the user's password is correct.  Get their reason and add
            try:
                user_reason = ReasonConjunction.objects.get(target=dataset + '/contributor/' + user)
            except DoesNotExist:
                return rc.FORBIDDEN
        else:
            #incorrect password
            return rc.FORBIDDEN
        
        mqlquery = MQLQuery.make(query_args, result_args)
        
        assertions_from_freebase = mqlquery.get_results(dataset, user, polarity, context, True)
        
        return '{Added/voted for %s assertions from freebase for %s}'%(str(len(assertions_from_freebase)),str(query_args))
    
    def db_merge(self, request, obj_url):
        
        db1 = request.POST['database1']
        db2 = request.POST['database2']
        dataset = request.POST.get('dataset', 'None')
        user = request.POST['user']
        password = request.POST['password']
        
        if dataset == 'None':
            dataset = None
        
        if User.objects.get(username=user).check_password(password):
            merge(db1, db2, dataset)

        else:
            #incorrect password
            return rc.FORBIDDEN
        
        return "Merge successful."
        