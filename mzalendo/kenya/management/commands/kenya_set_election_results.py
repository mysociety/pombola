# This command is for updating the aspirants in Mzalendo from the IEBC
# API - it relies on already-imported aspirants having the external_id
# field of their Position set to the IEBC candidate code.

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

before_import_date = datetime.date(2013, 2, 7)

future_approximate_date = ApproximateDate(future=True)

data_directory = os.path.join(sys.path[0], 'kenya', '2013-election-data')

class Command(NoArgsCommand):
    help = 'Find the successful candidate in each area, and update positions'

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

        # To get all the candidates, we iterate over each county,
        # constituency and ward, and request the candidates for each.

        cache_directory = os.path.join(data_directory, 'api-cache-2013-03-06')

        mkdir_p(cache_directory)

        same_person_checker = SamePersonChecker(os.path.join(data_directory,
                                                             'names-manually-checked.csv'))

        failed = False

        for area_type in 'county', 'constituency', 'ward':

            cache_filename = os.path.join(cache_directory, area_type + '.json')
            area_type_data = get_data_with_cache(cache_filename, url('/%s/' % (area_type)))
            areas = area_type_data['region']['locations']
            area_name_to_codes = defaultdict(list)
            # Unfortunately areas with the same name appear multiple
            # times in these results:
            for area in areas:
                area_name_to_codes[area['name']].append(area)

            area_place_kind = PlaceKind.objects.get(name__iexact=area_type)
            race_types = [k for k, v in known_race_type_mapping.items() if v[0] == area_place_kind]

            for area_name, areas in area_name_to_codes.items():
                print "=======", area_type, area_name
                if len(areas) > 1:
                    print "There were multiple areas for the", area_type, area_name
                    for area in areas:
                        print "  ", area['name'], place_code
                for area in areas:
                    place_code = area['code']
                    for race_type_number in race_types:
                        results_data_filename = os.path.join(cache_directory, 'results-for-%s-%s-%s.json' % (area_type, race_type_number, place_code))
                        try:
                            results_url = url('/results/%s/%s/' % (area_type, place_code),
                                              query_filter='post=' + race_type_number)
                            results_data = get_data_with_cache(results_data_filename, results_url)
                        except ValueError, ve:
                            print "Getting results failed for", area_type, area_name, "for contest", race_type_number
                            print ve
                            continue

                        # FIXME: to complete - each candidate has a
                        # code field, and this should be used to find
                        # the corresponding aspirant position in
                        # Mzalendo's database.  Then the successful
                        # aspirant should have a new non-aspirant
                        # position created, while the other aspirants
                        # should just have an end date set for their
                        # aspirant position.
