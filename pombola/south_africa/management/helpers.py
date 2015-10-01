from collections import defaultdict
from difflib import SequenceMatcher
from itertools import chain
import json
import math
import os
import re
import requests
import time
import urllib

from django.db.models import Q

from mapit.models import Generation, Area, Code

from pombola.core.models import Position

def fix_province_name(province_name):
    if province_name == 'Kwa-Zulu Natal':
        return 'KwaZulu-Natal'
    else:
        return province_name

def fix_municipality_name(municipality_name):
    if municipality_name == 'Merafong':
        return 'Merafong City'
    else:
        return municipality_name

def all_initial_forms(name, squash_initials=False):
    '''Generate all initialized variants of first names

    >>> for name in all_initial_forms('foo Bar baz quux', squash_initials=True):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    fB baz quux
    fBb quux

    >>> for name in all_initial_forms('foo Bar baz quux'):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    f B baz quux
    f B b quux
    '''
    names = name.split(' ')
    n = len(names)
    if n == 0:
        yield name
    for i in range(0, n):
        if i == 0:
            yield ' '.join(names)
            continue
        initials = [forename[0] for forename in names[:i]]
        if squash_initials:
            result = [''.join(initials)]
        else:
            result = initials
        yield ' '.join(result + names[i:])

class LocationNotFound(Exception):
    pass

def geocode(address_string, geocode_cache=None, verbose=True):
    if geocode_cache is None:
        geocode_cache = {}

    if address_string=='TBA':
        raise LocationNotFound

    # Try using Google's geocoder:
    geocode_cache.setdefault('google', {})
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
    url += urllib.quote(address_string.encode('UTF-8'))
    if url in geocode_cache['google']:
        result = geocode_cache['google'][url]
    else:
        r = requests.get(url)
        result = r.json()
        geocode_cache['google'][url] = result
        time.sleep(1.5)
    status = result['status']
    if status in ("ZERO_RESULTS", "UNKNOWN_ERROR"):
        raise LocationNotFound
    elif status == "OK":
        all_results = result['results']
        if len(all_results) > 1:
            # The ambiguous results here typically seem to be much of
            # a muchness - one just based on the postal code, on just
            # based on the town name, etc.  As a simple heuristic for
            # the moment, just pick the one with the longest
            # formatted_address:
            all_results.sort(key=lambda r: -len(r['formatted_address']))
            message = u"Warning: disambiguating %s to %s" % (address_string,
                                                             all_results[0]['formatted_address'])
            if verbose:
                print message.encode('UTF-8')
        # FIXME: We should really check the accuracy information here, but
        # for the moment just use the 'location' coordinate as is:
        geometry = all_results[0]['geometry']
        lon = float(geometry['location']['lng'])
        lat = float(geometry['location']['lat'])
        return lon, lat, geocode_cache

title_slugs = ('provincial-legislature-member',
               'committee-member',
               'alternate-member')

def get_na_member_lookup():
    # Build an list of tuples of (mangled_mp_name, person_object) for each
    # member of the National Assembly and delegate of the National Coucil
    # of Provinces:

    na_member_lookup = defaultdict(set)

    def warn_duplicate_name(name_form, person):
        try:
            message = "Tried to add '%s' => %s, but there were already '%s' => %s" % (
                name_form, person, name_form, na_member_lookup[name_form])
            print message
        except UnicodeDecodeError:
            print 'Duplicate name issue'

    people_done = set()
    for position in chain(Position.objects.filter(title__slug='member',
                                                  organisation__slug='national-assembly'),
                          Position.objects.filter(title__slug='member-of-the-provincial-legislature').currently_active(),
                          Position.objects.filter(title__slug='member',
                                                  organisation__kind__slug='provincial-legislature').currently_active(),
                          Position.objects.filter(title__slug__in=title_slugs).currently_active(),
                          Position.objects.filter(title__slug__startswith='minister').currently_active(),
                          Position.objects.filter(title__slug='delegate',
                                                  organisation__slug='ncop').currently_active()):

        person = position.person
        if person in people_done:
            continue
        else:
            people_done.add(person)
        for name in person.all_names_set():
            name = name.lower().strip()
            # Always leave the last name, but generate all combinations of initials
            name_forms = set(chain(all_initial_forms(name),
                                   all_initial_forms(name, squash_initials=True)))
            # If it looks as if there are three full names, try just
            # taking the first and last names:
            m = re.search(r'^(\S{4,})\s+\S.*\s+(\S{4,})$', name)
            if m:
                name_forms.add(u"{0} {1}".format(*m.groups()))
            for name_form in name_forms:
                if name_form in na_member_lookup:
                    warn_duplicate_name(name_form, person)
                na_member_lookup[name_form].add(person)

    return na_member_lookup

def get_mapit_municipality(municipality, province=''):
    municipality = fix_municipality_name(municipality)
    mapit_current_generation = Generation.objects.current()

    # If there's a municipality, try to add that as a place as well:
    mapit_municipalities = Area.objects.filter(
        Q(type__code='LMN') | Q(type__code='DMN'),
        generation_high__gte=mapit_current_generation,
        generation_low__lte=mapit_current_generation,
        name=municipality)

    mapit_municipality = None

    if len(mapit_municipalities) == 1:
        mapit_municipality = mapit_municipalities[0]
    elif len(mapit_municipalities) == 2:
        # This is probably a Metropolitan Municipality, which due to
        # https://github.com/mysociety/pombola/issues/695 will match
        # an LMN and a DMN; just pick the DMN:
        if set(m.type.code for m in mapit_municipalities) == set(('LMN', 'DMN')):
            mapit_municipality = [m for m in mapit_municipalities if m.type.code == 'DMN'][0]
        else:
            # Special cases for 'Emalahleni' and 'Naledi', which
            # are in multiple provinces:
            if municipality == 'Emalahleni':
                if province=='Mpumalanga':
                    mapit_municipality = Code.objects.get(type__code='l', code='MP312').area
                elif province=='Eastern Cape':
                    mapit_municipality = Code.objects.get(type__code='l', code='EC136').area
                else:
                    raise Exception, "Unknown Emalahleni province %s" % (province)
            elif municipality == 'Naledi':
                if province=='Northern Cape':
                    mapit_municipality = Code.objects.get(type__code='l', code='NW392').area
                else:
                    raise Exception, "Unknown Naledi province %s" % (province)
            else:
                raise Exception, "Ambiguous municipality name '%s'" % (municipality,)
    return mapit_municipality

# Given a name string, try to find a person from the Pombola database
# that matches that as closely as possible.  Note that if the form of
# the name supplied matches more than one person, it's arbitrary which
# one you'll get back.  This doesn't happen in the South Africa data
# at the moment, but that's still a FIXME (probably by replacing this
# with PopIt's name resolution).

def find_pombola_person(name_string, na_member_lookup, verbose=True):
    # Strip off any phone number at the end, which sometimes include
    # NO-BREAK SPACE or a / for multiple numbers.
    name_string = re.sub(r'(?u)[\s\d/]+$', '', name_string).strip()
    # And trim any list numbers from the beginning:
    name_string = re.sub(r'^[\s\d\.]+', '', name_string)
    # Strip off some titles:
    name_string = re.sub(r'(?i)^(Min|Dep Min|Dep President|President) ', '', name_string)
    name_string = name_string.strip()
    if not name_string:
        return None
    # Move any initials to the front of the name:
    name_string = re.sub(r'^(.*?)(([A-Z] *)*)$', '\\2 \\1', name_string)
    name_string = re.sub(r'(?ms)\s+', ' ', name_string).strip().lower()
    # Score the similarity of name_string with each person:
    scored_names = []
    for actual_name, people in na_member_lookup.items():
        for person in people:
            t = (SequenceMatcher(None, name_string, actual_name).ratio(),
                 actual_name,
                 person)
            scored_names.append(t)
    scored_names.sort(reverse=True, key=lambda n: n[0])
    # If the top score is over 90%, it's very likely to be the
    # same person with the current set of MPs - this leave a
    # number of false negatives from misspellings in the CSV file,
    # though.
    if scored_names[0][0] >= 0.9:
        return scored_names[0][2]
    else:
        if verbose:
            print "Failed to find a match for " + name_string.encode('utf-8')
        return None

geocode_cache_filename = os.path.join(
    os.path.dirname(__file__),
    '.geocode-request-cache')

def get_geocode_cache():
    try:
        with open(geocode_cache_filename) as fp:
            return json.load(fp)
    except IOError:
        return {}

def write_geocode_cache(geocode_cache):
    with open(geocode_cache_filename, "w") as fp:
        json.dump(geocode_cache, fp, indent=2)

def debug_location_change(location_from, location_to):

    #calculate the distance between the points to
    #simplify determining whether the cause is a minor
    #geocode change using the haversine formula
    #http://www.movable-type.co.uk/scripts/latlong.html
    r = 6371
    lat1 = math.radians(location_from.y)
    lat2 = math.radians(location_to.y)
    delta_lat = math.radians(location_to.y-location_from.y)
    delta_lon = math.radians(location_to.x-location_from.x)

    a = math.sin(delta_lat/2)**2 + \
        math.cos(lat1) * math.cos(lat2) * \
        math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));

    d = r * c;

    print "%s km https://www.google.com/maps/dir/'%s,%s'/'%s,%s'/" % (d, location_from.y, location_from.x, location_to.y, location_to.x)
