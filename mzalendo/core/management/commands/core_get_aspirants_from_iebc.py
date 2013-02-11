from collections import defaultdict
import csv
import errno
import hmac
import hashlib
import itertools
import json
import os
import re
import requests
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.template.defaultfilters import slugify

from settings import IEBC_API_ID, IEBC_API_SECRET
from optparse import make_option

from core.models import Place, PlaceKind, Person, ParliamentarySession, PositionTitle

iebc_base_url = 'http://api.iebc.or.ke'

# Calling these 'corrections' may not be quite right.  There are
# naming discrepancies between the documents published by the IEBC and
# the IEBC API in spellings of ward names in particular.  This maps
# the IEBC API version to what we have in the API (which for wards was
# derived from "Final Constituencies and Wards Description.pdf").

place_name_corrections = {'LUNGALUNGA': 'Lunga Lunga'}

with open('wards-names-matched.csv') as fp:
    reader = csv.reader(fp)
    for api_name, db_name in reader:
        if api_name and db_name:
            place_name_corrections[api_name] = db_name

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

def get_person_from_names(first_names, surname):
    full_name = first_names + ' ' + surname
    first_and_last = re.sub(' .*', '', first_names) + ' ' + surname
    for field in 'legal_name', 'other_names':
        for version in (full_name, first_and_last):
            kwargs = {field + '__iexact': version}
            matches = Person.objects.filter(**kwargs)
            if len(matches) > 1:
                message = "Multiple Person matches for %s against %s" % (version, field)
                print >> sys.stderr, message
                # raise Exception, message
            elif len(matches) == 1:
                return matches[0]
    # Otherwise, look for the best hits using Levenshtein distance:
    for field in 'legal_name', 'other_names':
        for version in (full_name, first_and_last):
            closest_match = Person.objects.raw('SELECT *, levenshtein(legal_name, %s) AS difference FROM core_person ORDER BY difference LIMIT 1', [version])[0]
            if closest_match.difference <= 2:
                print "  good closest match to %s against %s was: %s (with score %d)" % (field, version, closest_match, closest_match.difference)
    return None

def get_matching_place(place_name, place_kind, parliamentary_session):
    place_name_to_use = place_name_corrections.get(place_name, place_name)
    # We've normalized ward names to have a single space on either
    # side of a / or a -, so change API ward names to match:
    if place_kind.slug in ('ward', 'county'):
        place_name_to_use = re.sub(r'(\w) *([/-]) *(\w)', '\\1 \\2 \\3', place_name_to_use)

    print "place_name_to_use is:", place_name_to_use
    # As with other place matching scripts here, look for the
    # slugified version to avoid problems with different separators:
    place_slug = slugify(place_name_to_use)
    if place_kind.slug == 'ward':
        place_slug = 'ward-' + place_slug
    elif place_kind.slug == 'county':
        place_slug += '-county'
    elif place_kind.slug == 'constituency':
        place_slug += '-2013'
    print 'using slug:', place_slug
    matching_places = Place.objects.filter(slug=place_slug,
                                           kind=place_kind,
                                           parliamentary_session=parliamentary_session)
    if not matching_places:
        raise Exception, "Found no place that matched: '%s' <%s> <%s>" % (place_name, place_kind, parliamentary_session)
    elif len(matching_places) > 1:
        raise Exception, "Multiple places found that matched: '%s' <%s> <%s> - they were: %s" % (place_name, place_kind, parliamentary_session, ",".join(str(p for p in matching_places)))
    else:
        return matching_places[0]

def parse_race_name(known_race_types, race_name):
    print "parsing: '%s'" % (race_name,)
    types_alternation = "|".join(re.escape(krt) for krt in known_race_types)
    m = re.search('^((%s) - )(.*?)\s+\(\d+\)$' % (types_alternation,), race_name)
    if not m:
        raise Exception, "Couldn't parse race:" + race_name
    return (m.group(2), m.group(3))

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

        def url(path, query_filter=None):
            """A closure to avoid repeating parameters"""
            return make_api_url(path, IEBC_API_SECRET, token, query_filter)

        # Since the following things don't work with the API:
        #
        #   - Requesting all contests via /contest/
        #   - Requesting candidates for a particular constituency, ward or
        #     county via /candidate/ with a query filter
        #
        # ... the simplest approach to getting all candidate data is
        # to request all parties, and then request all candidates for
        # each party.

        cache_directory = os.path.join(sys.path[0], 'cache')
        candidates_cache_directory = os.path.join(cache_directory, 'candidatates-by-party')
        parties_cache_filename = os.path.join(cache_directory, 'parties')

        mkdir_p(cache_directory)

        # Get all the parties:

        party_data = get_data_with_cache(parties_cache_filename, url('/party/'))

        # Now that we've got all the parties, request all the
        # candidates for each party:

        for d in party_data['parties']:
            code = d['code']
            candidates_cache_filename = os.path.join(cache_directory, 'candidates-for-' + code)
            candidate_data = get_data_with_cache(candidates_cache_filename, url('/candidate/', query_filter='party=%s' % (code,)))
            for race in candidate_data['candidates']:
                race_name = race['race']
                candidates = race['candidates']
                print len(candidates), race_name


        return






        # Try to get all the contests:

        contest_data = get_data(url('/contest/'))
        print contest_data

        # As of 2013-02-07 there are no contests defined by the API


        # Just as an example, get all the counties:
        county_data = get_data(url('/county/'))

        # print "got county_data:", county_data['region']['locations']
        for county in county_data['region']['locations']:
            print 'county is', county
            name = county['name']
            code = county['code']
            print "got", name, code


            candidate_url = url('/candidates/', query_filter='county=%s' % (code,))
            print "candidate_url is:", candidate_url
            candidate_data = get_data(candidate_url)
            print candidate_data
            break




















        # Just as an example, get all the counties:
        constituency_data = get_data(url('/constituency/'))

        # print "got constituency_data:", constituency_data['region']['locations']
        for constituency in constituency_data['region']['locations']:
            print 'constituency is', constituency
            name = constituency['name']
            code = constituency['code']
            print "got", name, code

            candidate_data = get_data(url('/candidates/', query_filter='constituency=%s' % (code,)))
            print candidate_data
            break








        return


        # Just as an example, get all the wards:
        if False:
            ward_data = get_data(url('/ward/'))

            wards_from_api = sorted(ward['name'].encode('utf-8') for ward in ward_data['region']['locations'])
            wards_from_db = sorted(p.name.encode('utf-8') for p in Place.objects.filter(kind__slug='ward'))

            both = itertools.izip_longest(wards_from_api, wards_from_db)

            with open('wards-names.csv', 'w') as fp:
                writer = csv.writer(fp)
                for t in both:
                    writer.writerow(t)

        # party_data = get_data(url('/party/'))
        # for d in party_data['parties']:
        #     print d['name']
        # print "(That's", len(party_data['parties']), "parties)"

        # Try to get all the Presidential Aspirants:

        # FIXME: just try to get all candidates to start with:

        cached_filename = 'candidates.json'

        if os.path.exists(cached_filename):
            with open(cached_filename) as fp:
                candidate_data = json.load(fp)
        else:
            candidate_data = get_data(url('/candidate/'))
            with open(cached_filename, 'w') as fp:
                json.dump(candidate_data, fp)

        candidate_counts = defaultdict(int)

        for race in candidate_data['candidates']:
            race_name = race['race']
            candidate_counts[race_name] += 1

        # for race_name, n in sorted(candidate_counts.items(), key=lambda x: (x[1], x[0])):
        #     print n, race_name

        # So far, we have:
        #   1420 County Assembly Rep races (one per ward? we have 1407 wards)
        #   46 Governor races (one missing?)
        #   284 National Assembly Rep races (one per constituency? 6 missing)
        #   46 Senator races (one missing?)
        #   46 Women Representative races (one missing?)
        #
        # For the counties, Nairobi (and Diaspora) are missing in each case...

        governor_counties = set()

        for race in candidate_data['candidates']:
            race_name = race['race']
            m = re.search('^(Governor - )(.*)\(\d+\)$', race_name)
            # m = re.search('^(Senator - )(.*)\(\d+\)$', race_name)
            # m = re.search('^(Women Representative - )(.*)\(\d+\)$', race_name)
            if m:
                governor_counties.add(slugify(m.group(2)))

        county_data = get_data(url('/county/'))
        api_county_names = set(slugify(d['name']) for d in county_data['region']['locations'])

        print "Counties that only have governor races"
        for c in governor_counties - api_county_names:
            print "  ", c

        print "Counties that are only in the API:"
        for c in api_county_names - governor_counties:
            print "  ", c


        # Set up a mapping between the race names and the
        # corresponding PlaceKind and Position title:

        known_race_type_mapping = {
            "Governor": (PlaceKind.objects.get(slug='county'),
                         ParliamentarySession.objects.get(slug='s2013'),
                         PositionTitle.objects.filter(slug__startswith='aspirant-governor')),
            "Senator": (PlaceKind.objects.get(slug='county'),
                        ParliamentarySession.objects.get(slug='s2013'),
                        PositionTitle.objects.filter(slug__startswith='aspirant-senator')),
            "Women Representative": (PlaceKind.objects.get(slug='county'),
                                     ParliamentarySession.objects.get(slug='s2013'),
                                     PositionTitle.objects.filter(slug__startswith='aspirant-women-representative')),
            "National Assembly Rep.": (PlaceKind.objects.get(slug='constituency'),
                                       ParliamentarySession.objects.get(slug='na2013'),
                                       PositionTitle.objects.filter(slug__startswith='aspirant-mp')),
            "County Assembly Rep.": (PlaceKind.objects.get(slug='ward'),
                                     ParliamentarySession.objects.get(slug='na2013'),
                                     PositionTitle.objects.filter(slug__startswith='aspirant-governor')),
            }

        known_race_types = known_race_type_mapping.keys()

        for race in candidate_data['candidates']:

            full_race_name = race['race']
            race_type, place_name = parse_race_name(known_race_types, full_race_name)

            # Get the type of place from the name of the race:

            place_kind, session, title = known_race_type_mapping[race_type]

            place = get_matching_place(place_name, place_kind, session)


            print "looking for", place_name
            print "  got place:", place
#             number_of_candidates = len(race['candidates'])
#             if number_of_candidates > 0:
#                 # print number_of_candidates, race_name
#                 for candidate in race['candidates']:
#                     print "Trying to match:", candidate['other_name'], candidate['surname']
#                     person = get_person_from_names(candidate['other_name'], candidate['surname'])
#                     if person:
#                         print "  got:", person








        return

        # Just as an example, get all the counties:
        county_data = get_data(url('/county/'))

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
        nairobi_county_data = get_data(url('/county/%s/' % (nairobi_county_code,)))

        print "not nairobi_county_data:", nairobi_county_data

        # Now try to get all constituencies within Nairobi, which uses
        # a query_filter:

        constituencies_in_nairobi = get_data(url('/constituency/',
                                                 query_filter='county=%s' % (nairobi_county_code,)))

        print len(constituencies_in_nairobi['region']['locations']), "constituencies in Nairobi county:"

        # Just as an example, get all the counties:
        constituency_data = get_data(url('/constituency/'))

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


