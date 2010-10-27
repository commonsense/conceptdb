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

def lookup_reason(reason_id):
  return _get_json('reason', reason_id)

def lookup_factor_targets(factor_name):
  return _get_json('factorusedfor', factor_name[1:]) #strip leading '/' from factor_name

def find_assertion(dataset, relation, concepts, polarity = 1, context = 'None'):
    url_append = 'assertionfind?dataset=' + dataset + '&rel=' + relation + '&concepts=' + concepts + '&polarity=' + str(polarity) + '&context=' + context
    return _get_json_with_queries(url_append)

def lookup_concept(concept_name, start = 0, limit = 10):
    return _get_json_with_queries('conceptfind' + concept_name + '?start=' + str(start) + '&limit=' + str(limit))

def lookup_expression(expression_id):
    return _get_json('expression', expression_id)

def lookup_assertion_expressions(assertion_id, start = 0, limit = 10):
    return _get_json_with_queries('assertionexpressions?id=' + str(assertion_id) + '&start=' + str(start) + '&limit=' + str(limit))

def _get_json(*url_parts):
    url = API_URL + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '?format=json'
    return json.loads(_get_url(url))


def _get_json_with_queries(*url_parts):
    url = API_URL + '/'.join(p for p in url_parts) + '&format=json'
    print url
    return json.loads(_get_url(url))

def _get_url(url):
    conn = urllib2.urlopen(url)
    return conn.read()
