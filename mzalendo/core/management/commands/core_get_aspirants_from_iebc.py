from collections import defaultdict
import csv
import datetime
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

from django_date_extensions.fields import ApproximateDate

from settings import IEBC_API_ID, IEBC_API_SECRET
from optparse import make_option

from core.models import Place, PlaceKind, Person, ParliamentarySession, Position, PositionTitle, Organisation, OrganisationKind

from iebc_api import *

new_data_date = datetime.date(2013, 2, 8)
new_data_approximate_date = ApproximateDate(new_data_date.year,
                                            new_data_date.month,
                                            new_data_date.day)

data_directory = os.path.join(sys.path[0], 'kenyan-election-data')

# Calling these 'corrections' may not be quite right.  There are
# naming discrepancies between the documents published by the IEBC and
# the IEBC API in spellings of ward names in particular.  This maps
# the IEBC API version to what we have in the API (which for wards was
# derived from "Final Constituencies and Wards Description.pdf").

place_name_corrections = {}

with open(os.path.join(data_directory, 'wards-names-matched.csv')) as fp:
    reader = csv.reader(fp)
    for api_name, db_name in reader:
        if api_name and db_name:
            place_name_corrections[api_name] = db_name

party_name_corrections = {}

with open(os.path.join(data_directory, 'party-names-matched.csv')) as fp:
    reader = csv.reader(fp)
    for api_name, db_name in reader:
        if api_name and db_name:
            party_name_corrections[api_name] = db_name

same_people = {}

names_checked_csv_file = 'names-manually-checked.csv'
with open(os.path.join(data_directory, names_checked_csv_file)) as fp:
    reader = csv.DictReader(fp)
    for row in reader:
        classification = row['Same/Different']
        mz_id = int(row['Mz ID'], 10)
        candidate_code = row['API Candidate Code']
        key = (candidate_code, mz_id)
        if re.search('^Same', classification):
            same_people[key] = True
        elif re.search('^Different', classification):
            same_people[key] = False
        else:
            raise Exception, "Bad 'Same/Different' value in the line: %s" % (row,)

def get_matching_party(party_name, **options):
    party_name_to_use = party_name_corrections.get(party_name, party_name)
    # print "looking for '%s'" % (party_name_to_use,)
    matching_parties = Organisation.objects.filter(kind__slug='party',
                                                   name__iexact=party_name_to_use)
    if not matching_parties:
        matching_parties = Organisation.objects.filter(kind__slug='party',
                                                       name__istartswith=party_name_to_use)
    if len(matching_parties) == 0:
        party_name_for_creation = party_name_to_use.title()
        new_party = Organisation(name=party_name_for_creation,
                                 slug=slugify(party_name_for_creation),
                                 started=ApproximateDate(datetime.date.today().year),
                                 ended=None,
                                 kind=OrganisationKind.objects.get(slug='party'))
        maybe_save(new_party, **options)
        return new_party
    elif len(matching_parties) == 1:
        return matching_parties[0]
    else:
        raise Exception, "Multiple parties matched %s" % (party_name_to_use,)

def get_matching_place(place_name, place_kind, parliamentary_session):
    place_name_to_use = place_name_corrections.get(place_name, place_name)
    # We've normalized ward names to have a single space on either
    # side of a / or a -, so change API ward names to match:
    if place_kind.slug in ('ward', 'county'):
        place_name_to_use = re.sub(r'(\w) *([/-]) *(\w)', '\\1 \\2 \\3', place_name_to_use)
    # As with other place matching scripts here, look for the
    # slugified version to avoid problems with different separators:
    place_slug = slugify(place_name_to_use)
    if place_kind.slug == 'ward':
        place_slug = 'ward-' + place_slug
    elif place_kind.slug == 'county':
        place_slug += '-county'
    elif place_kind.slug == 'constituency':
        place_slug += '-2013'
    matching_places = Place.objects.filter(slug=place_slug,
                                           kind=place_kind,
                                           parliamentary_session=parliamentary_session)
    if not matching_places:
        raise Exception, "Found no place that matched: '%s' <%s> <%s>" % (place_slug, place_kind, parliamentary_session)
    elif len(matching_places) > 1:
        raise Exception, "Multiple places found that matched: '%s' <%s> <%s> - they were: %s" % (place_slug, place_kind, parliamentary_session, ",".join(str(p for p in matching_places)))
    else:
        return matching_places[0]

def parse_race_name(known_race_types, race_name):
    types_alternation = "|".join(re.escape(krt) for krt in known_race_types)
    m = re.search('^((%s) - )(.*?)\s+\(\d+\)$' % (types_alternation,), race_name)
    if not m:
        raise Exception, "Couldn't parse race:" + race_name
    return (m.group(2), m.group(3))

def make_new_person(candidate, **options):
    legal_name = (candidate.get('other_name', None) or '').title()
    if legal_name:
        legal_name += ' '
    legal_name += candidate['surname'].title()
    new_person = Person(legal_name=legal_name, slug=slugify(legal_name))
    maybe_save(new_person, **options)
    return new_person

def update_parties(person, api_party, **options):
    current_party_positions = person.position_set.all().currently_active().filter(title__slug='member').filter(organisation__kind__slug='party')
    if 'name' in api_party:
        # Then we should be checking that a valid party membership
        # exists, or create a new one otherwise:
        api_party_name = api_party['name']
        mz_party = get_matching_party(api_party_name, **options)
        need_to_create_party_position = True
        for party_position in (p for p in current_party_positions if p.organisation == mz_party):
            # If there's a current position in this party, that's fine
            # - just make sure that the end_date is 'future':
            party_position.end_date = ApproximateDate(future=True)
            maybe_save(party_position, **options)
            need_to_create_party_position = False
        for party_position in (p for p in current_party_positions if p.organisation != mz_party):
            # These shouldn't be current any more - end them when we
            # got the new data:
            party_position.end_date = new_data_approximate_date
            maybe_save(party_position, **options)
        if need_to_create_party_position:
            new_position = Position(title=PositionTitle.objects.get(name='Member'),
                                    organisation=mz_party,
                                    category='political',
                                    person=person,
                                    start_date=new_data_approximate_date,
                                    end_date=ApproximateDate(future=True))
            maybe_save(new_position, **options)
    else:
        # If there's no party specified, end all current party positions:
        for party_position in current_party_positions:
            party_position.end_date = new_data_approximate_date
            maybe_save(party_position, **options)

def maybe_save(o, **options):
    if options['commit']:
        o.save()
        print >> sys.stderr, 'Saving %s' % (o,)
    else:
        print >> sys.stderr, 'Not saving %s because --commit was not specified' % (o,)

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

        aspirants_to_remove = set(Position.objects.all().aspirant_positions().exclude(title__slug__iexact='aspirant-president').currently_active())

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

        # To get all the candidates, we iterate over each county,
        # constituency and ward, and request the candidates for each.

        cache_directory = os.path.join(sys.path[0], 'cache')

        mkdir_p(cache_directory)

        total_candidates = 0
        race_type_counts = defaultdict(int)

        headings = ['API Name',
                    'API Party',
                    'API Place',
                    'API Candidate Code',
                    'Mz Legal Name',
                    'Mz Other Names',
                    'Mz URL',
                    'Mz Parties Ever',
                    'Mz Aspirant Ever',
                    'Mz Politician Ever',
                    'Mz ID']

        with open(os.path.join(sys.path[0], 'names-to-check.csv'), 'w') as fp:

            writer = csv.DictWriter(fp, headings)

            writer.writerow(dict((h, h) for h in headings))

            for area_type in 'county', 'constituency', 'ward':
                cache_filename = os.path.join(cache_directory, area_type)
                area_type_data = get_data_with_cache(cache_filename, url('/%s/' % (area_type)))
                areas = area_type_data['region']['locations']
                for i, area in enumerate(areas):
                    # Get the candidates for that area:
                    code = area['code']
                    candidates_cache_filename = os.path.join(cache_directory, 'candidates-for-' + area_type + '-' + code)
                    candidate_data = get_data_with_cache(candidates_cache_filename, url('/candidate/', query_filter='%s=%s' % (area_type, code)))
                    # print "got candidate_data:", candidate_data
                    for race in candidate_data['candidates']:
                        full_race_name = race['race']
                        race_type, place_name = parse_race_name(known_race_types, full_race_name)
                        place_kind, session, title = known_race_type_mapping[race_type]
                        place = get_matching_place(place_name, place_kind, session)
                        candidates = race['candidates']
                        for candidate in candidates:
                            first_names = candidate['other_name'] or ''
                            surname = candidate['surname'] or ''
                            race_type_counts[race_type] += 1
                            person = get_person_from_names(first_names, surname)
                            print "returned person is:", person
                            if person:
                                try:
                                    same_person = same_people[(candidate['code'], person.id)]
                                except KeyError:
                                    print >> sys.stderr, "No manually checked information found about the detected match between:"
                                    print >> sys.stderr, candidate
                                    print >> sys.stderr, person
                                    raise Exception, "No manually checked information found"
                                if not same_person:
                                    person = None
                            # Now we know we need to create a new Person:
                            if not person:
                                person = make_new_person(candidate, **options)
                            update_parties(person, candidate['party'], **options)

                            # Now we just need to make sure that there's an appropriate aspirant position, which will be defined by:
                            #   - the place
                            #   - the organisation (REPUBLIC OF KENYA used in most cases)

                            aspirant_position_properties = {
                                'organisation': Organisation.objects.get(name='REPUBLIC OF KENYA'),
                                'place': place,
                                'person': person,
                                'title': title,
                                'category': 'political'}

                            existing_matching_aspirant_positions = Position.objects.filter(**aspirant_position_properties).currently_active()

                            for existing_matching_aspirant_position in existing_matching_aspirant_positions:
                                # These are still valid, so don't remove them:
                                aspirants_to_remove.discard(existing_matching_aspirant_position)

                            if not existing_matching_aspirant_positions:
                                new_position = Position(start_date=new_data_approximate_date,
                                                        end_date=ApproximateDate(future=True),
                                                        **aspirant_position_properties)
                                maybe_save(new_position, **options)

                            total_candidates += 1

        for aspirant_to_remove in aspirants_to_remove:
            if options['commit']:
                aspirants_to_remove.delete()

        print "total_candidates by area are:", total_candidates

        for race_type, count in race_type_counts.items():
            print race_type, count

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



        if False:
            party_names_api = set(d['name'].strip().encode('utf-8') for d in party_data['parties'])
            party_names_db = set(o.name.strip().encode('utf-8') for o in Organisation.objects.filter(kind__slug='party'))

            with open(os.path.join(data_directory, 'party-names.csv'), 'w') as fp:
                writer = csv.writer(fp)
                for t in itertools.izip_longest(party_names_api, party_names_db):
                    writer.writerow(t)


        # Just as an example, get all the wards:
        if False:
            ward_data = get_data(url('/ward/'))

            wards_from_api = sorted(ward['name'].encode('utf-8') for ward in ward_data['region']['locations'])
            wards_from_db = sorted(p.name.encode('utf-8') for p in Place.objects.filter(kind__slug='ward'))

            with open(os.path.join(data_directory, 'wards-names.csv'), 'w') as fp:
                writer = csv.writer(fp)
                for t in itertools.izip_longest(wards_from_api, wards_from_db):
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


