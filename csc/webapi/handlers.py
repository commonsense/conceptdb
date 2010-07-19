from piston.handler import BaseHandler, rc
from csc.conceptdb.assertion import Assertion, Sentence
from csc.conceptdb.metadata import Dataset
from csc.conceptdb.justify import Justification,Reason
import mongoengine as mon
from mongoengine.queryset import DoesNotExist

BASE = "" #TODO: get base URL

class DatasetHandler(BaseHandler):
    """A GET request to this URL will show the dataset's language and name"""

    allowed_methods = ('GET',)
    model = Dataset

    @throttle(600,60,'read')
    def read(self, request, dataset):
        try:
            dataset = Dataset.objects.get(name=dataset)
            return {'name':dataset.name, 'lang':dataset.language}
        except DoesNotExist:
            return rc.NOT_FOUND


class AssertionFindHandler(BaseHandler):
    """GET request w/dataset, argstr, rel shows assertion's information if it exists"""

    allowed_methods = ('GET',)
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

class AssertionHandler(BaseHandler):
    """GET request returns information about assertion w/id"""
    
    allowed_methods = ('GET',)
    model = Assertion

    @throttle(200,60,'read'):
    def read(self, request, id):
        try:
            assertion = Assertion.objects.get(id = id)
            return assertion
        except DoesNotExist:
            return rc.NOT_FOUND


class AssertionCreateHandler(BaseHandler):
    """Lookup Assertion.  If it does not exist, create it with reason based on
    the user and location it was submitted from.  If it does exist, add the
    user and location reason to its justification."""

    allowed_methods = ('PUT',)
    model = Assertion

    @throttle(200,60,'update')
    def update(self, request, dataset, relation, argstr, polarity = 1, context = None):
        pass
        #TODO: implement
