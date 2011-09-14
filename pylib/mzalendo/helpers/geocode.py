
import urllib
import re

from django.conf import settings

import httplib2
h = httplib2.Http( settings.HTTPLIB2_CACHE_DIR )

# In Python 2.6 simplejson is json in the standard library. In 2.5 it was still 
# simplejson. Cope with either.
try:
    import json
except ImportError:
    import simplejson as json 

KENYA_BOUNDS = '-5,33.5|5,44'

common_parameters = {
    'sensor': 'false',
}

GEOCODE_URL = 'http://maps.googleapis.com/maps/api/geocode/json?%s'

def find(address, bounds=KENYA_BOUNDS):
    # At some point, this should probably become a proper wrapper
    # for the google geocoding.
    parameters = dict(address=address,bounds=bounds)
    parameters.update(common_parameters)

    param_string = urllib.urlencode(parameters)

    url = GEOCODE_URL %param_string

    response, content = h.request(url)
    json_content = json.loads(content)

    try:
        # Let's assume for the moment that the first location in the
        # list is the best one.
        raw_results = json_content['results']
        
        # import pprint
        # pprint.pprint( raw_results )
        
        results = []

        for r in raw_results:
            
            # If result not in Kenya skip it
            if r['address_components'][-1]['short_name'] != 'KE':
                continue
            
            # cleanup the name
            name = r['formatted_address']
            name = re.sub( r', Kenya$', '', name )

            # check that we don't alreadiy have an entry for that name
            if name in [ existing['name'] for existing in results ]:
                continue

            results.append(
                {
                    'name': name,
                    'lat':  reduce_precision( r['geometry']['location']['lat'] ),
                    'lng':  reduce_precision( r['geometry']['location']['lng'] ),
                }
            )
        # results = result[0]['geometry']['location']
    except IndexError:
        results = []

    return results

def reduce_precision(value):
    """Return the value to only 5 decimal places, and convert to string"""
    return "%.5f" % value



def coord_to_areas( lat, lng ):
    """Turn the coordinates given into areas"""
    data = get_mapit_url( 'point', [ 4326, '%s,%s'%(lng,lat) ] )
    
    # Filter it down to the areas that we want
    wanted_area_codes = set( ['PRO','DIV'] )

    return_data = {}

    for key, value in data.items():
        if value['type'] not in wanted_area_codes: continue

        return_data[ value['type'] ] = {
            'name': # Given unique look-up attributes, and extra data attributes,
            # either updates the entry referred to if it exists, or
            # creates it if it doesn't.
            # Returns string describing what has happened.
            value['name'],
            'mapit_id': value['id'],
        }

    return return_data


def get_mapit_url( method, args ):
    """Create a url and return the decoded JSON data from it"""

    # print args
    url_args = [ urllib.quote( str(i) ) for i in args ]

    join_args = [settings.MAPIT_URL, method ]
    join_args.extend( url_args )

    mapit_url = '/'.join( join_args )
    # print mapit_url

    response, content = h.request( mapit_url )
    data = json.loads(content)
    
    # delete the debug info straight away
    del( data['debug_db_queries'] )    

    return data

    