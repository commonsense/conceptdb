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
        try:
            return Dataset.get(obj_url).serialize()
        except DoesNotExist:
            return rc.NOT_FOUND

    def assertionLookup(self, obj_url):
        try:
            return Assertion.get(obj_url.replace('/assertion/', '')).serialize()    
        except DoesNotExist:
            return rc.NOT_FOUND

    def assertionFind(self, request, obj_url):
        dataset = request.GET['dataset']
        relation = request.GET['rel']
        argstr = request.GET['concepts']
        polarity = int(request.GET['polarity'])
        context = request.GET['context']
        
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
        return ExternalReason.get(obj_url.replace('/reason','')).serialize()

    def assertionMake(self, request, obj_url):
        """This method takes the unique identifiers of an assertion as its arguments:
        """
        dataset = request.POST['dataset']
        relation = request.POST['rel']
        argstr = request.POST['concepts']
        arguments = argstr.split(',')
        polarity = int(request.POST['polarity'])
        context = request.POST['context']

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

            return assertion


    def assertionVote(self, request, obj_url):

        if obj_url.startswith('/assertionvote'):
            dataset = request.POST['dataset']
            relation = request.POST['rel']
            argstr = request.POST['concepts']
            polarity = int(request.POST['polarity'])
            context = request.POST['context']

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

        return assertion
