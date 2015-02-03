import requests
import time
import urllib


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
        initials = [name[0] for name in names[:i]]
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
