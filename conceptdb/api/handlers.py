from piston.handler import BaseHandler
from piston.utils import throttle, rc
from conceptdb.assertion import Assertion, Sentence
from conceptdb.metadata import Dataset, ExternalReason
import conceptdb
from mongoengine.queryset import DoesNotExist


conceptdb.connect_to_mongodb('test')

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
            return self.assertionFind(request, obj_url)
        elif obj_url.startswith('/reason'):
            return self.reasonLookup(obj_url)
        elif obj_url.startswith('/concept'):
            return self.conceptLookup(request, obj_url)
        
        return {'message': 'you are looking for %s' % obj_url}

    @throttle(200,60,'update')
    def create(self, request, obj_url):
        #can start with /assertionmake or /assertionvote.  If assertionmake,
        #looks for the assertion.  If can't find, makes it and contributes
        #a positive vote.  

        #if assertionvote, looks for the assertion and votes on it.  If it can't find
        #it nothing happens
        obj_url = '/' + obj_url
        if obj_url.startswith('/assertionmake'):
            return self.assertionMake(request, obj_url)
        elif obj_url.startswith('/assertionvote') or obj_url.startswith('/assertionidvote'):
            return self.assertionVote(request, obj_url)
    
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
        polarity = int(request.GET.get('polarity',1))
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

    def reasonLookup(self, obj_url):
        """Method allows you to look up an External Reason by its name.  
        Accessed by going to URL /api/reason/{name}
        """

        return ExternalReason.get(obj_url.replace('/reason','')).serialize()

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

        cursor = Assertion.objects._collection.find({'arguments':obj_url}).skip(start).limit(limit)
        assertions = "["

        i = start
        while (i < start + limit):
            try:
                assertions = assertions + str(cursor.next()) + ", "
            except StopIteration:
                break #no more assertions within the skip/limit boundaries
            i += 1
        
        assertions = assertions[:len(assertions) - 2] #strip last ', '
        assertions = assertions + "]"

        if i == start: #no assertions were found for the concept
            return rc.NOT_FOUND

        return assertions

    def assertionMake(self, request, obj_url):
        """This method takes the unique identifiers of an assertion as its arguments:
        dataset, relation, concepts, context, and polarity.  It checks to see if this
        assertion exists.  If it does not, it creates it and adds the submitting user's
        vote as a justification.  If it exists already, it adds the submitting user's
        vote as a justification.

        Accessed by going to the URL
        /api/assertionmake?dataset={dataset}&rel={relation}&concepts={concept1,concept2,etc}&
        polarity={polarity}&context={context}

        Polarity and context are optional, defaulting to polarity = 1 context = None
        """
        dataset = request.POST['dataset']
        relation = request.POST['rel']
        argstr = request.POST['concepts']
        arguments = argstr.split(',')
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

            assertion.add_support([]) #TODO: base on user's Reason

            return "The assertion you created already exists.  Your vote for this \
            assertion has been counted.\n" + assertion.serialize()

        except DoesNotExist:
            assertion = Assertion.make(dataset = dataset,
                        arguments = arguments,
                        relation = relation,
                        polarity = polarity,
                        context = context)

            assertion.add_support([]) #TODO: base on user's reason

            return assertion.serialize()


    def assertionVote(self, request, obj_url):
        """Assertion vote is called whenever someone is voting on an assertion.  It can 
        be accessed in one of 2 ways: voting on an assertion identified directly by its id
        or voting on an assertion identified by its unique attributes. To add a positive vote,
        the user should make vote=1.  A negative vote is vote=-1.  Any other values will result
        in no action being taken.  

        Can be accessed through either of the following URLS:
        /api/assertionvote?dataset={dataset}&rel={relation}&concept={concept1,concept2,etc}
        &polarity={polarity}&context={context}&vote={vote}

        polarity and context are optional values, defaulting to polarity = 1 and context = None

        /api/assertionidvote?id={id}&vote={vote}
        """

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
            except DoesNotExist:
                return rc.NOT_FOUND

        vote = request.POST['vote']

        if vote == "1": #vote in favor
            assertion.add_support([]) #TODO: base on user's reason
        elif vote == "-1": #vote against
            assertion.add_oppose([]) #TODO: base on user's reason
        else: #invalid vote
            return {"message":"Vote value invalid."}

        return assertion.serialize()
