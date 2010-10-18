"""
A basic rest client for the conceptdb web api.  

Based on rest client for conceptnet 4

"""

import urllib2

try:
    import json
except:
    import simplejson as json


SERVER_URL = 'http://127.0.0.1:8000' #NOTE: testing.  
API_URL = 'http://127.0.0.1:8000/api/'
CLIENT_VERSION = '1'


def lookup_assertion(assertion_id):
    return _get_json('assertion', assertion_id)

def lookup_dataset(dataset_name):
    dataset_name = dataset_name[1:] #strip leading '/'
    return _get_json(dataset_name)

#FIXME: figure out why this is returning 500
def find_assertion(dataset, relation, concepts, polarity = '1.0', context = 'None'):
    dataset = dataset.replace('/', '%2F')
    concepts = concepts.replace('/', '%2F')
    relation = relation.replace('/', '%2F')
    url_append = 'assertionfind?dataset=' + dataset + '&rel=' + relation + '&concepts=' + concepts + '&polarity=' + polarity + '&context=' + context
    return _get_json(url_append)

def _get_json(*url_parts):
    url = API_URL + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '?format=json'
    print("url = " + str(url))
    return json.loads(_get_url(url))


def _get_url(url):
    conn = urllib2.urlopen(url)
    return conn.read()
