# This script is intended to patch the data originally loaded in using the
# south_africa_import_constituency_offices command. When this was originally run
# the DA offices (or constituency areas) had not been geolocated. This script
# reads in a CSV with the list of offices and the location information and for
# each entry tries to find a database entry to update.
#
# The CSV can be obtained by downloading it from
# https://docs.google.com/spreadsheet/ccc?key=0Am9Hd8ELMkEsdHpOUjBvNVRzYlN4alRORklDajZwQlE
#
# The expected CSV headers (first row of CSV file) are:
#
#    Party Code
#    Name
#    Party
#    Manually Geocoded LonLat
#
# Other columns will be ignored.
#
# The organisation name will be used to create a slug, and this is used to
# search for a matching entry in the database.

# from collections import defaultdict, namedtuple
import csv
# from difflib import SequenceMatcher
# from itertools import chain
# import json
from optparse import make_option
# import os
import re
# import requests
# import sys
# import time
# import urllib
#
# from django.conf import settings
# from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
# from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, CommandError
# from django.db.models import Q
from django.template.defaultfilters import slugify
#
from pombola.core.models import (OrganisationKind, Organisation, PlaceKind,
                         ContactKind, OrganisationRelationshipKind,
                         OrganisationRelationship, Identifier, Position,
                         PositionTitle, Person)
#
# from mapit.models import Generation, Area, Code

VERBOSE = False

def verbose(message):
    if VERBOSE:
        print message

class Command(LabelCommand):
    """Add locations to DA constituency areas"""

    help = 'Add locations to DA constituency areas'

    option_list = LabelCommand.option_list + (
        make_option(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Output extra information for debugging'),
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_label(self, input_filename, **options):

        global VERBOSE
        VERBOSE = options['verbose']

        ok_constituency_area, _ = OrganisationKind.objects.get_or_create(
            slug='constituency-area',
            name='Constituency Area')

        # pk_constituency_area, _ = PlaceKind.objects.get_or_create(
        #     slug='constituency-area',
        #     name='Constituency Area')

        with open(input_filename) as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                # Make sure there's no leading or trailing
                # whitespace, and we have unicode strings:
                row = dict((k, row[k].decode('UTF-8').strip()) for k in row)

                # Extract each column:
                party_code = row['Party Code']
                name = row['Name']
                party = row['Party']
                lonlat = row['Manually Geocoded LonLat']

                # only interested in entries that have been geocoded
                if not lonlat:
                    continue

                abbreviated_party = party
                m = re.search(r'\((?:|.*, )([A-Z\+]+)\)', party)
                if m:
                    abbreviated_party = m.group(1)

                # Collapse whitespace in the name to a single space:
                name = re.sub(r'(?ms)\s+', ' ', name)

                if party_code:
                    organisation_name = "%s Constituency Area (%s): %s" % (abbreviated_party, party_code, name)
                else:
                    organisation_name = "%s Constituency Area: %s" % (abbreviated_party, name)
                organisation_slug = slugify(organisation_name)

                # Search for the area in the database via the constituency area organisation kind
                org_qs = ok_constituency_area.organisation_set.all().filter(slug=organisation_slug)

                if not org_qs.exists():
                    print "No match found for " + organisation_name
                    continue

                org = org_qs[0]
                print u"Found match {0} for {1}".format(org, organisation_name)

                # get the place associated
                places = org.place_set.all()
                
                # check that we have exactly one place to work with
                if not places.count() == 1:
                    raise "Got wrong number of places, expected 1"

                place = places[0]
                
                lon, lat = map(float, lonlat.split(","))
                point = Point(x=lon, y=lat, srid=4326)

                

                if options['commit']:
                    place.location = point
                    place.save()
