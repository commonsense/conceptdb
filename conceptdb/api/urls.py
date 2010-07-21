from django.conf.urls.defaults import *
from piston.resource import Resource
#from csc.webapi.docs import documentation_view
from conceptdb.api.handlers import *

# This gives a way to accept "query.foo" on the end of the URL to set the
# format to 'foo'. "?format=foo" works as well.
Q = r'(query\.(?P<emitter_format>.+))?$'

urlpatterns = patterns('',
    url(r'api/(?P<obj_url>.+)'+Q,
        Resource(ConceptDBHandler), name='conceptdb_handler'))

# :vim:tw=0:nowrap:
