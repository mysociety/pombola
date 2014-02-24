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

from django.conf import settings
from optparse import make_option

from pombola.core.models import Place, PlaceKind, Person, ParliamentarySession, Position, PositionTitle, Organisation, OrganisationKind

from iebc_api import *

before_import_date = datetime.date(2013, 2, 7)

future_approximate_date = ApproximateDate(future=True)

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
        print >> sys.stderr, "* Creating a new party because none matched '%s'" % (party_name_to_use,)
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

def make_new_person(candidate, **options):
    legal_name = normalize_name((candidate.get('other_name', None) or '').title())
    if legal_name:
        legal_name += ' '
    legal_name += normalize_name((candidate.get('surname', None) or '').title())
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
        api_party_name = api_party['name']
    else:
        api_party_name = 'Independent Aspirant'
        # If there's a current assignment to another party, issue a warning:
        current_party_assignments = [p for p in current_party_positions if p.organisation.slug != 'independent-aspirant']
        if current_party_assignments:
            print "Not resetting to Independent Aspirant someone who's in a party %s: %s" % (person, current_party_assignments)
            return
    # Then we should be checking that a valid party membership
    # exists, or create a new one otherwise:
    mz_party = get_matching_party(api_party_name, **options)
    need_to_create_party_position = True
    for party_position in (p for p in current_party_positions if p.organisation == mz_party):
        # If there's a current position in this party, that's fine
        # - just make sure that the end_date is 'future':
        if party_position.end_date != future_approximate_date:
            party_position.end_date = future_approximate_date
            print >> sys.stderr, "* Setting a party position end_date to 'future' for %s in %s" % (person, api_party)
            maybe_save(party_position, **options)
        need_to_create_party_position = False
    for party_position in (p for p in current_party_positions if p.organisation != mz_party):
        # These shouldn't be current any more - end them when we
        # got the new data:
        party_position.end_date = yesterday_approximate_date
        print >> sys.stderr, "* Ending a party position yesterday for %s: no longer in %s" % (person, party_position.organisation)
        maybe_save(party_position, **options)
    if need_to_create_party_position:
        new_position = Position(title=PositionTitle.objects.get(name='Member'),
                                organisation=mz_party,
                                category='political',
                                person=person,
                                start_date=today_approximate_date,
                                end_date=future_approximate_date)
        print >> sys.stderr, "* Creating a party position that needs to exist: %s should be in %s" % (person, mz_party)
        maybe_save(new_position, **options)

def update_candidates_for_place(place_name,
                                place_kind,
                                parliamentary_session,
                                title,
                                race_type,
                                candidates,
                                same_person_checker,
                                **options):

    all_updates_succeeded = True

    place = get_matching_place(place_name, place_kind, parliamentary_session)

    current_aspirants = Position.objects.filter(place=place, title=title).currently_active()
    
    print "%s %s %s %s %s" % (place_name,
                              place_kind,
                              parliamentary_session,
                              title,
                              race_type)

    def full_name(c):
        return normalize_name(c['other_name']) + " " + normalize_name(c['surname'])

    code_to_existing_aspirant = dict((a.external_id, a) for a in current_aspirants if a.external_id)
    code_to_current_candidates = dict((c['code'], c) for c in candidates)

    existing_aspirant_codes = set(code_to_existing_aspirant.keys())
    current_candidate_codes = set(code_to_current_candidates.keys())

    existing_aspirants_to_remove = existing_aspirant_codes - current_candidate_codes
    new_candidates_to_add = current_candidate_codes - existing_aspirant_codes

    matched_candidate_codes = current_candidate_codes & existing_aspirant_codes

    # Add each candidate that wasn't already present:

    for code in new_candidates_to_add:
        candidate = code_to_current_candidates[code]
        first_names = normalize_name(candidate['other_name'] or '')
        surname = normalize_name(candidate['surname'] or '')
        person = get_person_from_names(first_names, surname)
        # If that person was an existing current aspirant, they'll
        # just need to have the IEBC candidate code set:
        iebc_code_just_needed_setting = False
        for matching_existing_aspirant_position in current_aspirants.filter(person=person):
            if matching_existing_aspirant_position.external_id:
                if matching_existing_aspirant_position.external_id != code:
                    print "     original: '%s'" % (matching_existing_aspirant_position.external_id,)
                    print "    candidate: '%s'" % (code,)
                    format_tuple = (matching_existing_aspirant_position.person,
                                    matching_existing_aspirant_position.external_id,
                                    person,
                                    code)
                    message = "There was an existing candidate (%s - %s) with a name match for (%s - %s) but different codes" % format_tuple
                    # raise Exception, message
                    print message
            else:
                matching_existing_aspirant_position.external_id = code
                print >> sys.stderr, "* The IEBC code was missing for %s" % (matching_existing_aspirant_position,)
                maybe_save(matching_existing_aspirant_position, **options)
                update_parties(person, candidate['party'], **options)
                iebc_code_just_needed_setting = True
        if iebc_code_just_needed_setting:
            continue
        # If we have a person match, but they weren't a current
        # aspirant in this race, then be careful that we're not
        # mismatching using the SamePersonChecker:
        if person:
            same_person = same_person_checker.check_same_and_update(candidate,
                                                                    place,
                                                                    race_type,
                                                                    person)
            if same_person is None:
                all_updates_succeeded = False
                continue
        if not person:
            print >> sys.stderr, "* Creating a person because none matched %s %s" % (first_names, surname)
            person = make_new_person(candidate, **options)

        assert(person)

        update_parties(person, candidate['party'], **options)

        aspirant_position_properties = {
            'organisation': Organisation.objects.get(name='REPUBLIC OF KENYA'),
            'place': place,
            'person': person,
            'title': title,
            'category': 'political'}

        # First see if that aspirant position already exists:
        existing_matching_aspirant_positions = Position.objects.filter(**aspirant_position_properties).currently_active()

        if existing_matching_aspirant_positions:
            # If it does, make sure that the IEBC code is set in
            # external_id, and that the end_date is 'future':
            for existing_matching_aspirant_position in existing_matching_aspirant_positions:
                if existing_matching_aspirant_position.external_id != code or existing_matching_aspirant_position.end_date != future_approximate_date:
                    print >> sys.stderr, "* Need to set either the IEBC code or the end date (future) for %s" % (existing_matching_aspirant_position,)
                    existing_matching_aspirant_position.external_id = code
                    existing_matching_aspirant_position.end_date = future_approximate_date
                    maybe_save(existing_matching_aspirant_position, **options)
        else:
            # Then we have to create a new position:
            new_position = Position(start_date=today_approximate_date,
                                    end_date=future_approximate_date,
                                    external_id=code,
                                    **aspirant_position_properties)
            print >> sys.stderr, "* Creating a missing position: %s" % (new_position,)
            maybe_save(new_position, **options)

    # For those aspirants that are no longer current, end their aspirant position:

    for code in existing_aspirants_to_remove:
        existing_aspirant_to_remove = code_to_existing_aspirant[code]
        print >> sys.stderr, "* Removing a no longer current aspirant: %s (position id: %s)" % (existing_aspirant_to_remove, existing_aspirant_to_remove.id,)
        existing_aspirant_to_remove.end_date = yesterday_approximate_date
        maybe_save(existing_aspirant_to_remove, **options)

    # For those aspirants that were already present, just make sure
    # their party assignments are correct:

    for code in matched_candidate_codes:
        # Make sure that the party assignments are correct:
        person = code_to_existing_aspirant[code].person
        candidate = code_to_current_candidates[code]
        update_parties(person, candidate['party'], **options)

    return all_updates_succeeded

def get_contest_type(candidates):
    distinct_contest_types = set(c['contest_type'] for c in candidates)
    contest_type = iter(distinct_contest_types).next()
    return contest_type

#     old_aspirants.sort(key=lambda x: x.lower())
# 
#     print "%s %s %s %s %s %d" % (place_name,
#                                  place_kind,
#                                  parliamentary_session,
#                                  title,
#                                  race_type,
#                                  len(candidates))
#     print "######## Old:"
#     for aspirant in old_aspirants:
#         print "  ", aspirant, "(IEBC: %s)" % (aspirant.external_id)
#     print "######## New:"
#     for aspirant in new_aspirants:
#         print "  ", aspirant, "(IEBC: %s)" % (aspirant.external_id)
#     print "------------------------------------------------------------------------"
#     for candidate in candidates:
#         print "  ", normalize_name(candidate['other_name']), normalize_name(candidate['surname'])

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

        aspirants_to_remove = set(Position.objects.all().aspirant_positions().exclude(title__slug__iexact='aspirant-president').currently_active())

        # To get all the candidates, we iterate over each county,
        # constituency and ward, and request the candidates for each.

        cache_directory = os.path.join(data_directory, 'api-cache-2013-03-01')

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

            for area_name, areas in area_name_to_codes.items():
                all_candidates = defaultdict(list)
                for area in areas:
                    place_code = area['code']
                    candidates_cache_filename = os.path.join(cache_directory, 'candidates-for-' + area_type + '-' + place_code + '.json')
                    candidate_data = get_data_with_cache(candidates_cache_filename, url('/candidate/', query_filter='%s=%s' % (area_type, place_code)))
                    races = candidate_data['candidates']
                    for race in races:
                        candidates = race['candidates']
                        if not candidates:
                            continue
                        contest_type = get_contest_type(candidates)
                        all_candidates[contest_type] += race['candidates']
                for contest_type, candidates in all_candidates.items():
                    place_kind, session, title, race_type = known_race_type_mapping[contest_type]
                    succeeded = update_candidates_for_place(area_name,
                                                            place_kind,
                                                            session,
                                                            title,
                                                            race_type,
                                                            candidates,
                                                            same_person_checker,
                                                            **options)
                    if not succeeded:
                        failed = True

                    # Try to update the picture for each candidate:
                    for candidate in candidates:
                        update_picture_for_candidate(candidate, cache_directory, **options)

        if failed:
            print "Failed: you need to update", same_person_checker.csv_filename
