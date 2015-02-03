from collections import defaultdict
from itertools import chain
import re
import requests
import time
import urllib

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
    url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
    url += urllib.quote(address_string.encode('UTF-8'))
    if url in geocode_cache['google']:
        result = geocode_cache['google'][url]
    else:
        r = requests.get(url)
        result = r.json()
        geocode_cache['google'][url] = result
        time.sleep(1.5)
    status = result['status']
    if status == "ZERO_RESULTS":
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
