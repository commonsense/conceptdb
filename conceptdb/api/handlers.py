from piston.handler import BaseHandler
from piston.utils import throttle, rc
from conceptdb.assertion import Assertion, Sentence
from conceptdb.metadata import Dataset, ExternalReason
from conceptdb.justify import Justification
import conceptdb
from mongoengine.queryset import DoesNotExist


conceptdb.connect_to_mongodb('test')

class ConceptDBHandler(BaseHandler):
    """A GET request to this can show the info for a dataset or assertion"""

    allowed_methods = ('GET',)

    @throttle(600,60,'read')
    def read(self, request, obj_url):
        obj_url = '/'+obj_url

        if obj_url.startswith('/data'):#try to find matching dataset
            try:
                return Dataset.get(obj_url).serialize()
            except DoesNotExist:
                return rc.NOT_FOUND
        elif obj_url.startswith('/assertion/'):
            #matches /assertion/id, look up by id
            try:
                return Assertion.get(obj_url.replace('/assertion/', '')).serialize()    
            except DoesNotExist:
                return rc.NOT_FOUND
        elif obj_url.startswith('/assertionfind'):
            #currently info is in form:
            #/assertionfind/rel/argstr/polarity/context/dataset
            #dataset is at end because URL form means unsure where
            #to delimit it
            
            args = obj_url.split('/',6) #only split at 6 because
            #any '/' after that are part of the dataset name
            #args = ["","assertionfind","rel","argstr","polarity","context","dataset"]
            if args[5] == "None":
                args[5] = None
            try:
                return Assertion.objects.get(
                    dataset = args[6],
                    relation= args[2],
                    argstr = args[3],
                    polarity =int(args[4]),
                    context = args[5]).serialize()
            except DoesNotExist:
                return rc.NOT_FOUND
        elif obj_url.startswith('/reason'):
            return ExternalReason.get(obj_url.replace('/reason','')).serialize()
                     
        return {'message': 'you are looking for %s' % obj_url}



class AssertionFindHandler(BaseHandler):
    """GET request w/dataset, argstr, rel shows assertion's information if it exists"""

    allowed_methods = ('GET','PUT',)
    model = Assertion

    @throttle(200,60,'read')
    def read(self, request, dataset, relation, argstr, polarity = 1, context = None):
        #currently assuming that argstr is given in sanitized form

        try:
            assertion = Assertion.objects.get(
                dataset = dataset,
                relation = relation,
                argstr = argstr,
                polarity = polarity,
                context = context
                )
            return assertion
        except DoesNotExist:
            return rc.NOT_FOUND

    @throttle(200,60,'update')
    def update(self, request, dataset, relation, argstr, polarity = 1, context = None,
        support=True):
        """Look up the assertion.  If it does not exist, create it and assign
        the user's justification.  If it does exist, add the user's justification
        to the assertion's justification tree."""

        try:
            assertion = Assertion.objects.get(
                dataset = dataset,
                relation = relation,
                argstr = argstr,
                polarity = polarity,
                context = context
                )
            if(support):
                assertion.justification.add_support([]) #TODO: implement
            else:
                assertion.justification.add_oppose([]) #TODO: implement
        except DoesNotExist:
            pass
            #TODO: implement
            

class AssertionHandler(BaseHandler):
    """GET request returns information about assertion w/id"""
    
    allowed_methods = ('GET',)
    model = Assertion

    @throttle(200,60,'read')
    def read(self, request, id):
        try:
            assertion = Assertion.objects.get(id = id)
            return assertion
        except DoesNotExist:
            return rc.NOT_FOUND


