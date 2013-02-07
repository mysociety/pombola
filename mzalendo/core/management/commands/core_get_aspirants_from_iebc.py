import requests
import hmac
import hashlib
import json
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.template.defaultfilters import slugify

from settings import IEBC_API_ID, IEBC_API_SECRET
from optparse import make_option

from core.models import Place

iebc_base_url = 'http://api.iebc.or.ke'

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
    data = json.loads(r.text)
    if data['status'] != 'SUCCESS':
        print >> sys.stderr, '  ', data['status']
        print >> sys.stderr, '  ', data['message']
        print >> sys.stderr, '  The URL was:', url
        raise CommandError, "Getting data from the API failed"
    return data

class Command(NoArgsCommand):
    help = 'Update the database with aspirants from the IEBC website'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        api_key = hmac.new(IEBC_API_SECRET,
                           "appid=%s" % (IEBC_API_ID,),
                           hashlib.sha256).hexdigest()

        token_data = get_data(make_api_token_url(IEBC_API_ID, api_key))
        token = token_data['token']

        # Just as an example, get all the counties:
        county_data = get_data(make_api_url('/county/', IEBC_API_SECRET, token))

        print "got county_data:", county_data.keys()

        print json.dumps(county_data['region'], indent=4)

        print "number of counties was:", len(county_data['region']['locations'])

        api_county_names = set(slugify(d['name']) for d in county_data['region']['locations'])
        db_county_names = set(slugify(p.name) for p in Place.objects.filter(kind__slug='county'))

        print "Counties that are only in the API:"
        for c in api_county_names - db_county_names:
            print "  ", c

        print "Counties that are only in the DB:"
        for c in db_county_names - api_county_names:
            print "  ", c

        # Try to get a particular county:

        nairobi_county_code='0188D30F-5258-45B8-86F2-D6185B21884A'
        nairobi_county_data = get_data(make_api_url('/county/%s/' % (nairobi_county_code,),
                                                    IEBC_API_SECRET, token))


        print "not nairobi_county_data:", nairobi_county_data

        # Now try to get all constituencies within Nairobi, which uses
        # a query_filter:

        constituencies_in_nairobi = get_data(make_api_url('/constituency/',
                                                          IEBC_API_SECRET,
                                                          token,
                                                          query_filter='county=%s' % (nairobi_county_code)))

        print len(constituencies_in_nairobi['region']['locations']), "constituencies in Nairobi county:"

        # Just as an example, get all the counties:
        constituency_data = get_data(make_api_url('/constituency/', IEBC_API_SECRET, token))

        print "got constituency_data:", constituency_data['region']['locations']
        print "length is:", len(constituency_data['region']['locations'])

        api_constituency_names = set(slugify(d['name']) for d in constituency_data['region']['locations'])
        db_constituency_names = set(slugify(p.name) for p in Place.objects.filter(kind__slug='constituency', parliamentary_session__slug='na2013'))

        print "Constituencies that are only in the API:"
        for c in api_constituency_names - db_constituency_names:
            print "  ", c

        print "Constituencies that are only in the DB:"
        for c in db_constituency_names - api_constituency_names:
            print "  ", c
