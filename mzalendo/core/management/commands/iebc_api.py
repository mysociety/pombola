import errno
import hmac
import hashlib
import json
import os
import re
import requests
import sys

from django.template.defaultfilters import slugify

from core.models import Person, Place, PlaceKind, ParliamentarySession, Position, PositionTitle

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
        if kwargs.get('only_from_cache', False):
            raise CommandError, "There was no cached data for %s" % (args[0],)
        else:
            result = get_data(*args, **kwargs)
            with open(cache_filename, 'w') as fp:
                json.dump(result, fp)
    return result

# ------------------------------------------------------------------------

# Set up a mapping between the race names and the
# corresponding PlaceKind and Position title:

known_race_type_mapping = {
    "Governor": (PlaceKind.objects.get(slug='county'),
                 ParliamentarySession.objects.get(slug='s2013'),
                 PositionTitle.objects.get(slug__startswith='aspirant-governor')),
    "Senator": (PlaceKind.objects.get(slug='county'),
                ParliamentarySession.objects.get(slug='s2013'),
                PositionTitle.objects.get(slug__startswith='aspirant-senator')),
    "Women Representative": (PlaceKind.objects.get(slug='county'),
                             ParliamentarySession.objects.get(slug='s2013'),
                             PositionTitle.objects.get(slug__startswith='aspirant-women-representative')),
    "National Assembly Rep.": (PlaceKind.objects.get(slug='constituency'),
                               ParliamentarySession.objects.get(slug='na2013'),
                               PositionTitle.objects.get(slug__startswith='aspirant-mp')),
    "County Assembly Rep.": (PlaceKind.objects.get(slug='ward'),
                             ParliamentarySession.objects.get(slug='na2013'),
                             PositionTitle.objects.get(slug__startswith='aspirant-ward-representative')),
    }

known_race_types = known_race_type_mapping.keys()

def parse_race_name(race_name):
    types_alternation = "|".join(re.escape(krt) for krt in known_race_types)
    m = re.search('^((%s) - )(.*?)\s+\(\d+\)$' % (types_alternation,), race_name)
    if not m:
        raise Exception, "Couldn't parse race:" + race_name
    return (m.group(2), m.group(3))

#------------------------------------------------------------------------

def get_person_from_names(first_names, surname):
    full_name = first_names + ' ' + surname
    first_and_last = re.sub(' .*', '', first_names) + ' ' + surname
    for field in 'legal_name', 'other_names':
        for version in (full_name, first_and_last):
            kwargs = {field + '__iexact': version}
            matches = Person.objects.filter(**kwargs)
            if len(matches) > 1:
                message = "  Multiple Person matches for %s against %s" % (version, field)
                print >> sys.stderr, message
                # raise Exception, message
            elif len(matches) == 1:
                return matches[0]
    # Or look for an exact slug match:
    matches = Person.objects.filter(slug=slugify(full_name))
    if len(matches) == 1:
        return matches[0]
    matches = Person.objects.filter(slug=slugify(first_and_last))
    if len(matches) == 1:
        return matches[0]
    return None
