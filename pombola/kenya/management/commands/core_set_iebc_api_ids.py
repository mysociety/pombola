# A one-off script to set the IEBC API codes in the external_id fields
# of places, organisations (parties) and positions (aspirant
# positions), to be run after core_import_aspirants_from_iebc - it has
# the same shape as that script, but just sets the external_id.

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

from django.conf import settings
from optparse import make_option

from pombola.core.models import Place, PlaceKind, Person, ParliamentarySession, Position, PositionTitle, Organisation, OrganisationKind

from iebc_api import *

new_data_date = datetime.date(2013, 2, 8)
new_data_approximate_date = ApproximateDate(new_data_date.year,
                                            new_data_date.month,
                                            new_data_date.day)

data_directory = os.path.join(sys.path[0], 'pombola', 'kenya', '2013-election-data')

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
        if options.get('create', True):
            party_name_for_creation = party_name_to_use.title()
            new_party = Organisation(name=party_name_for_creation,
                                     slug=slugify(party_name_for_creation),
                                     started=ApproximateDate(datetime.date.today().year),
                                     ended=None,
                                     kind=OrganisationKind.objects.get(slug='party'))
            maybe_save(new_party, **options)
            return new_party
        else:
            raise CommandError, "Would have to create %s, but 'create' was False" % (party_name,)
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

def make_new_person(candidate, **options):
    legal_name = (candidate.get('other_name', None) or '').title()
    if legal_name:
        legal_name += ' '
    legal_name += (candidate.get('surname', None) or '').title()
    slug_to_use = slugify(legal_name)
    suffix = 2
    while True:
        try:
            Person.objects.get(slug=slug_to_use)
        except Person.DoesNotExist:
            # Then this slug_to_use is fine, so just break:
            break
        slug_to_use = re.sub('-?\d*$', '', slug_to_use) + '-' + str(suffix)
        suffix += 1
    new_person = Person(legal_name=legal_name, slug=slug_to_use)
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

        parties_cache_filename = os.path.join(cache_directory, 'parties')
        party_data = get_data_with_cache(parties_cache_filename, url('/party/'), only_from_cache=True)
        for party in party_data['parties']:
            party_api_code = party['code']
            try:
                party_organisation = get_matching_party(party['name'], create=False, **options)
            except CommandError, ce:
                print >> sys.stderr, "Not setting the API code: %s" % (ce,)
            party_organisation.external_id = party_api_code
            maybe_save(party_organisation, **options)

        print "########################################################################"

        for area_type in 'county', 'constituency', 'ward':
            cache_filename = os.path.join(cache_directory, area_type)
            area_type_data = get_data_with_cache(cache_filename, url('/%s/' % (area_type)), only_from_cache=True)
            areas = area_type_data['region']['locations']
            for i, area in enumerate(areas):
                # Get the candidates for that area:
                code = area['code']
                candidates_cache_filename = os.path.join(cache_directory, 'candidates-for-' + area_type + '-' + code)
                candidate_data = get_data_with_cache(candidates_cache_filename, url('/candidate/', query_filter='%s=%s' % (area_type, code)), only_from_cache=True)
                # print "got candidate_data:", candidate_data
                for race in candidate_data['candidates']:
                    full_race_name = race['race']
                    race_type, place_name = parse_race_name(full_race_name)
                    place_kind, session, title = known_race_type_mapping[race_type]
                    place = get_matching_place(place_name, place_kind, session)
                    place.external_id = code
                    maybe_save(place, **options)
                    candidates = race['candidates']
                    for candidate in candidates:
                        first_names = candidate['other_name'] or ''
                        surname = candidate['surname'] or ''
                        person = get_person_from_names(first_names, surname)
                        if not person:
                            raise Exception, "Failed to find the person from '%s' '%s'" % (first_names, surname)
                        aspirant_position_properties = {
                            'organisation': Organisation.objects.get(name='REPUBLIC OF KENYA'),
                            'place': place,
                            'person': person,
                            'title': title,
                            'category': 'political'}
                        positions = Position.objects.filter(**aspirant_position_properties).currently_active()
                        if positions:
                            if len(positions) > 1:
                                print >> sys.stderr, "There were multiple (%d) matches for: %s" % (len(positions), aspirant_position_properties,)
                            for position in positions:
                                position.external_id = candidate['code']
                                maybe_save(position, **options)
                        else:
                            message = "There were no matches for %s" % (aspirant_position_properties,)
                            # raise Exception, message
                            print >> sys.stderr, message
