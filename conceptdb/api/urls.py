from django.conf.urls.defaults import *
from piston.resource import Resource
#from csc.webapi.docs import documentation_view
from handlers import *

# This gives a way to accept "query.foo" on the end of the URL to set the
# format to 'foo'. "?format=foo" works as well.
Q = r'(query\.(?P<emitter_format>.+))?$'

urlpatterns = patterns('',
    url(r'^data/(?P<dataset>[^/]+)/'+Q,
        Resource(DatasetHandler), name='dataset_handler'),
#    url(r'docs.txt$',
#        documentation_view, name='documentation_view')
)
# :vim:tw=0:nowrap:
