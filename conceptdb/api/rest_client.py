"""
A basic rest client for the conceptdb web api.  

Based on rest client for conceptnet 4

"""

import urllib2

try:
    import json
except:
    import simplejson as json


SERVER_URL = 'http://127.0.0.1:8000' #change when not testing
API_URL = 'http://127.0.0.1:8000/api/'
CLIENT_VERSION = '1'


def lookup_assertion(assertion_id):
    return _get_json('assertion', assertion_id)

def _get_json(*url_parts):
    url = API_URL + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '?format=json'
    return json.loads(_get_url(url))


def _get_url(url):
    conn = urllib2.urlopen(url)
    return conn.read()
