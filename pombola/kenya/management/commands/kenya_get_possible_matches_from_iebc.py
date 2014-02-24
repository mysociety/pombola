# This script generates mappings for parties, places and people
# between the IEBC API's names and those currently in Mzalendo.  The
# idea is to generate incorrect mappings for parties and places, and
# then fix the assignments using name_matcher.py.  Identifying people
# correctly is harder, so we instead we generate a CSV file of
# possible matches that can be uploaded to Google Spreadsheets for
# manual correction.

from collections import defaultdict
import csv
import datetime
import itertools
import json
import os
import re
import requests
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.template.defaultfilters import slugify

from django_date_extensions.fields import ApproximateDate

from django.conf import settings
from optparse import make_option

from pombola.core.models import Place, PlaceKind, Person, ParliamentarySession, Position, PositionTitle, Organisation, OrganisationKind

from iebc_api import *

data_directory = os.path.join(sys.path[0], 'kenya', '2013-election-data')

class Command(NoArgsCommand):
    help = 'Update the database with aspirants from the IEBC website'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        api_key = hmac.new(settings.IEBC_API_SECRET,
                           "appid=%s" % (settings.IEBC_API_ID,),
                           hashlib.sha256).hexdigest()

        token_data = get_data(make_api_token_url(settings.IEBC_API_ID, api_key))
        token = token_data['token']

        def url(path, query_filter=None):
            """A closure to avoid repeating parameters"""
            return make_api_url(path, settings.IEBC_API_SECRET, token, query_filter)

        # To get all the candidates, we iterate over each county,
        # constituency and ward, and request the candidates for each.

        cache_directory = os.path.join(data_directory, 'api-cache-2013-02-08')

        mkdir_p(cache_directory)

        # ------------------------------------------------------------------------

        print "Getting (incorrect) party names mapping for matching..."

        parties_cache_filename = os.path.join(cache_directory, 'parties')
        party_data = get_data_with_cache(parties_cache_filename, url('/party/'))

        party_names_api = set(d['name'].strip().encode('utf-8') for d in party_data['parties'])
        party_names_db = set(o.name.strip().encode('utf-8') for o in Organisation.objects.filter(kind__slug='party'))

        with open(os.path.join(data_directory, 'party-names.csv'), 'w') as fp:
            writer = csv.writer(fp)
            for t in itertools.izip_longest(party_names_api, party_names_db):
                writer.writerow(t)

        # ------------------------------------------------------------------------

        print "Getting (incorrect) ward names mapping for matching..."

        ward_data = get_data(url('/ward/'))

        wards_from_api = sorted(ward['name'].encode('utf-8') for ward in ward_data['region']['locations'])
        wards_from_db = sorted(p.name.encode('utf-8') for p in Place.objects.filter(kind__slug='ward'))

        with open(os.path.join(data_directory, 'wards-names.csv'), 'w') as fp:
            writer = csv.writer(fp)
            for t in itertools.izip_longest(wards_from_api, wards_from_db):
                writer.writerow(t)

        # ------------------------------------------------------------------------

        headings = ['Same/Different',
                    'API Name',
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
                    for race in candidate_data['candidates']:
                        full_race_name = race['race']
                        race_type, place_name = parse_race_name(full_race_name)
                        place_kind, session, title = known_race_type_mapping[race_type]
                        candidates = race['candidates']
                        for candidate in candidates:
                            first_names = candidate['other_name'] or ''
                            surname = candidate['surname'] or ''
                            person = get_person_from_names(first_names, surname)
                            if person:
                                print "Got person match to:", person
                                row = {}
                                row['Same/Different'] = ''
                                row['API Name'] = first_names + ' ' + surname
                                party_data = candidate['party']
                                row['API Party'] = party_data['name'] if 'name' in party_data else ''
                                row['API Place'] = '%s (%s)' % (place_name, area_type)
                                row['API Candidate Code'] = candidate['code']
                                row['Mz Legal Name'] = person.legal_name
                                row['Mz Other Names'] = person.other_names
                                row['Mz URL'] = 'http://info.mzalendo.com' + person.get_absolute_url()
                                row['Mz Parties Ever'] = ', '.join(o.name for o in person.parties_ever())
                                for heading, positions in (('Mz Aspirant Ever', person.aspirant_positions_ever()),
                                                           ('Mz Politician Ever', person.politician_positions_ever())):
                                    row[heading] = ', '.join('%s at %s' % (p.title.name, p.place) for p in positions)
                                row['Mz ID'] = person.id
                                for key, value in row.items():
                                    row[key] = unicode(value).encode('utf-8')
                                writer.writerow(row)
