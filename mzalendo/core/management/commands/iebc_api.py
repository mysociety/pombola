import errno
import hmac
import hashlib
import json
import os
import requests

iebc_base_url = 'http://api.iebc.or.ke'

# From: http://stackoverflow.com/q/600268/223092

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def make_api_token_url(app_id, api_key):
    """Create the URL that should be used for retrieving an API token"""

    return iebc_base_url + '/token/?appid=%s&key=%s' % (app_id, api_key)

def make_api_url(path, api_secret, token, query_filter=None):
    """Create a URL for a generic query to the API

    This can only be used after you've successfully got a token"""
    if query_filter is None:
        query_filter = ''
    key_string = '%stoken=%s' % (query_filter, token)
    key = hmac.new(api_secret,
                   key_string,
                   hashlib.sha256).hexdigest()
    url = iebc_base_url + path + '?'
    if query_filter:
        url += query_filter + '&'
    url += 'token=%s&key=%s' % (token, key)
    return url

def get_data(url):
    """Make a request to the API with error checking and JSON decoding"""

    r = requests.get(url)
    try:
        data = json.loads(r.text)
    except ValueError:
        print >> sys.stderr, "No valid JSON was found, the response was:"
        print >> sys.stderr, r.text
        raise
    if data['status'] != 'SUCCESS':
        print >> sys.stderr, '  ', data['status']
        print >> sys.stderr, '  ', data['message']
        print >> sys.stderr, '  The URL was:', url
        raise CommandError, "Getting data from the API failed"
    return data

def get_data_with_cache(cache_filename, *args, **kwargs):
    if os.path.exists(cache_filename):
        with open(cache_filename) as fp:
            result = json.load(fp)
    else:
        result = get_data(*args, **kwargs)
        with open(cache_filename, 'w') as fp:
            json.dump(result, fp)
    return result
