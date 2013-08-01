import csv
import json
import os
import re
import requests
import sys
import time
import urllib

from collections import defaultdict, namedtuple
from optparse import make_option

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, CommandError
from django.template.defaultfilters import slugify

from core.models import (OrganisationKind, Organisation, PlaceKind,
                         ContactKind, OrganisationRelationshipKind,
                         OrganisationRelationship)

from mapit.models import Generation, Area

class AmbiguousLocation(Exception):
    pass


class LocationNotFound(Exception):
    pass


def geocode(address_string, geocode_cache=None):
    if geocode_cache is None:
        geocode_cache = {}
    # Try using Google's geocoder:
    geocode_cache.setdefault('google', {})
    url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
    url += urllib.quote(address_string.encode('UTF-8'))
    if url in geocode_cache['google']:
        result = geocode_cache['google'][url]
    else:
        r = requests.get(url)
        result = r.json
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
            print message.encode('UTF-8')
        # FIXME: We should really check the accuracy information here, but
        # for the moment just use the 'location' coordinate as is:
        geometry = all_results[0]['geometry']
        lon = float(geometry['location']['lng'])
        lat = float(geometry['location']['lat'])
        return lon, lat, geocode_cache

def find_mzalendo_person(name_string, representative_type):
    return None

class Command(LabelCommand):
    """Import constituency offices"""

    help = 'Import constituency office data for South Africa'

    option_list = LabelCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_label(self, input_filename, **options):

        geocode_cache_filename = os.path.join(
            os.path.dirname(__file__),
            '.geocode-request-cache')

        try:
            with open(geocode_cache_filename) as fp:
                geocode_cache = json.load(fp)
        except IOError as e:
            geocode_cache = {}

        ok_party = OrganisationKind.objects.get(slug='party')
        ok_constituency_office = OrganisationKind.objects.get_or_create(
            slug='constituency-office',
            name='Constituency Office')
        ok_constituency_area = OrganisationKind.objects.get_or_create(
            slug='constituency-area',
            name='Constituency Area')

        pk_constituency_office = PlaceKind.objects.get_or_create(
            slug='constituency-office',
            name='Constituency Office')
        pk_constituency_area = PlaceKind.objects.get_or_create(
            slug='constituency-area',
            name='Constituency Area')

        ck_address = ContactKind.objects.get_or_create(
            slug='address',
            name='Address')

        ork_has_office = OrganisationRelationshipKind.objects.get_or_create(
            name='has_office')

        contact_source = "Data from the party via Geoffrey Kilpin"

        mapit_current_generation = Generation.objects.current()

        with_physical_addresses = 0
        geolocated = 0

        try:

            with open(input_filename) as fp:
                reader = csv.DictReader(fp)
                for row in reader:
                    # Make sure there's no leading or trailing
                    # whitespace, and we have unicode strings:
                    row = dict((k, row[k].decode('UTF-8').strip()) for k in row)
                    # Extract each column:
                    party_code = row['Party Code']
                    name = row['Name']
                    province = row['Province']
                    office_or_area = row['Type']
                    party = row['Party']
                    member_of_provincial_legislature = row['MPL']
                    member_of_provincial_legislature = row['MPL']
                    administrator = row['Administrator']
                    telephone = row['Tel']
                    fax = row['Fax']
                    physical_address = row['Physical Address']
                    postal_address = row['Postal Address']
                    email = row['E-mail']
                    municipality = row['Municipality']
                    wards = row['Wards']

                    name = re.sub(r'(?ms)\s+', ' ', name)

                    mz_party = Organisation.objects.get(name=party)

                    organisation_name = party + " office: " + name
                    organisation_slug = slugify(organisation_name)

                    places_to_add = []
                    contacts_to_add = []
                    people_to_add = []

                    if office_or_area == 'Office':
                        constituency_kind = ok_constituency_office
                        if physical_address:

                            # Sometimes there's lots of whitespace
                            # that splits the physical address from a
                            # P.O. Box address, so look for those cases:
                            pobox_address = None
                            m = re.search(r'(?ms)^(.*)\s{5,}(.*)$', physical_address)
                            if m:
                                physical_address = m.group(1).strip()
                                pobox_address = m.group(2).strip()

                            with_physical_addresses += 1
                            physical_address = physical_address.rstrip(',') + ", South Africa"
                            try:
                                print "physical_address:", physical_address.encode('UTF-8')
                                lon, lat, geocode_cache = geocode(physical_address, geocode_cache)
                                print "maps to:",
                                print "http://maps.google.com/maps?q=%f,%f" % (lat, lon)
                                geolocated += 1

                                place_name = u'Approximate position of ' + organisation_name
                                places_to_add.append({
                                        'name': place_name,
                                        'slug': slugify(place_name),
                                        'kind': pk_constituency_office,
                                        'location': Point(lon, lat)})

                                contacts_to_add.append({
                                        'kind': ck_address,
                                        'value': physical_address,
                                        'source': contact_source})

                            except LocationNotFound:
                                print "XXX no results found"

                            if pobox_address is not None:
                                contacts_to_add.append({
                                        'kind': ck_address,
                                        'value': pobox_address,
                                        'source': contact_source})

                    elif office_or_area == 'Area':
                        # At the moment it's only for DA that these
                        # Constituency Areas exist, so check that assumption:
                        if party != 'DA':
                            raise Exception, "Unexpected party %s with Area" % (party)
                        constituency_kind = ok_constituency_area
                        mapit_province = Area.objects.get(
                            type__code='PRV',
                            generation_high__gte=mapit_current_generation,
                            generation_low__lte=mapit_current_generation,
                            name=province)
                        place_name = 'Unknown sub-area of %s known as %s' % (
                            province,
                            organisation_name)
                        places_to_add.append({
                                'name': place_name,
                                'slug': slugify(place_name),
                                'kind': pk_constituency_area,
                                'mapit_area': mapit_province})

                        for representative_type in ('MP', 'MPL'):
                            person = find_mzalendo_person(row[representative_type],
                                                          representative_type)
                            if person:
                                people_to_add.append(mpl)

                    else:
                        raise Exception, "Unknown type %s" % (office_or_area,)

                    organisation_kwargs = {
                        'name': organisation_name,
                        'slug': slugify(organisation_name),
                        'kind': constituency_kind}

                    # Check if this office appears to exist already:

                    try:
                        if party_code:
                            # If there's something's in the "Party Code"
                            # column, we can check for an identifier:
                            identifier_schema = "constituency-office/%s/" % (party,)
                            identifier_identifier = party_code
                            org = Identifier.objects.get(identifier=identifier_identifier,
                                                         schema=identifier_schema).content_object
                        else:
                            # Otherwise use the slug we intend to use, and
                            # look for an existing organisation:
                            org = Organisation.objects.get(slug=organisation_slug,
                                                           kind=constituency_kind)
                    except ObjectDoesNotExist:
                        org = Organisation()

                    # Make sure we set the same attributes and save:
                    for k, v in organisation_kwargs:
                        setattr(org, k, v)
                    if options['commit']:
                        org.save()

                    # Replace all places associated with this
                    # organisation and re-add them:
                    if options['commit']:
                        org.place_set.all().delete()
                    for place_dict in places_to_add:
                        # FIXME: complete
                        pass
                    
                    # Replace all contact details associated with this
                    # organisation, and re-add them:
                    if options['commit']:
                        org.contacts.all().delete()
                    for contact_dict in contacts_to_add:
                        # FIXME: complete
                        pass

                    # Remove previous has_office relationships,
                    # between this office and any party, then re-add
                    # this one:
                    if options['commit']:
                        OrganisationRelationship.objects.filter(
                            organisation_b=org).delete()
                        OrganisationRelationship.objects.create(
                            organisation_a=mz_party,
                            kind=ork_has_office,
                            organisation_b=org)

                    # Remove all Membership relationships between this
                    # organisation and other people, then recreate them:

                    # TODO

        finally:
            with open(geocode_cache_filename, "w") as fp:
                json.dump(geocode_cache, fp, indent=2)

        print "Geolocated %d out of %d physical addresses" % (geolocated, with_physical_addresses)
