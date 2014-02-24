# A script which is designed to remove duplicate aspirants under very
# limited circumstances.  You almost certainly don't need (or want) to
# run this.

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
from django.contrib.contenttypes.models import ContentType

from django_date_extensions.fields import ApproximateDate

from django.conf import settings
from optparse import make_option

from pombola.core.models import Place, PlaceKind, Person, ParliamentarySession, Position, PositionTitle, Organisation, OrganisationKind, SlugRedirect

from iebc_api import *

before_import_date = datetime.datetime(2013, 2, 7, 0, 0, 0)

data_directory = os.path.join(sys.path[0], 'pombola', 'kenya', '2013-election-data')

place_name_corrections = {}

with open(os.path.join(data_directory, 'wards-names-matched.csv')) as fp:
    reader = csv.reader(fp)
    for api_name, db_name in reader:
        if api_name and db_name:
            place_name_corrections[api_name] = db_name

def person_replaces_other_person(person, other_person):
    matching_alternative_names = person.alternative_names.filter(alternative_name__iexact=other_person.legal_name)
    return bool(matching_alternative_names)

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

def remove_duplicate_candidates_for_place(place_name,
                                          place_kind,
                                          parliamentary_session,
                                          title,
                                          race_type,
                                          candidates,
                                          **options):

    place = get_matching_place(place_name, place_kind, parliamentary_session)
    current_aspirant_positions = Position.objects.filter(place=place, title=title).currently_active()

    # Create a person to position mapping to check for duplicate
    # positions for people:

    person_to_position = defaultdict(list)

    for current_aspirant_position in current_aspirant_positions.all():
        person = current_aspirant_position.person
        person_to_position[person].append(current_aspirant_position)

    for person, positions in person_to_position.items():
        if len(positions) > 1:
            # Then there are multiple positions for this person -
            # use a method for picking the best one that happens
            # to work for the 8 cases we have here; at the moment it's not
            positions.sort(key=lambda x: (x.external_id, x.start_date))
            best_position = positions[-1]
            for position in positions:
                if position != best_position:
                    if options['commit']:
                        position.delete()

    # Now look for current aspirant positions where the
    # alternative_name for its person is the legal_name of the person
    # associated with another current aspirant position - remove the
    # latter.

    real_person_to_others = defaultdict(set)

    for current_aspirant_position in current_aspirant_positions:
        other_aspirant_positions = set(current_aspirant_positions)
        other_aspirant_positions.discard(current_aspirant_position)

        for other_aspirant_position in other_aspirant_positions:
            current_person = current_aspirant_position.person
            other_person = other_aspirant_position.person
            if person_replaces_other_person(current_person, other_person):
                real_person_to_others[current_aspirant_position].add(other_aspirant_position)

    if real_person_to_others:
        print "------------------------------------------------------------------------"
        print "Removing duplicates for %s (%s)" % (place_name, race_type)
        removed_duplicate_position_for_same_person = False
        for real_person_position, other_position_set in real_person_to_others.items():
            if removed_duplicate_position_for_same_person:
                # We can't risk deleting both positions referring to
                # the same person, so if we've done one just break:
                break
            print real_person_position
            iebc_codes = set(op.external_id for op in other_position_set if op.external_id)
            for other_position in other_position_set:
                print "  <=", other_position
            if iebc_codes:
                if len(iebc_codes) > 1:
                    raise Exception, "Non-unique IEBC codes %s" % (iebc_codes,)
                else:
                    print "  IEBC codes were:", iebc_codes
                unique_iebc_code = iter(iebc_codes).next()
                if real_person_position.external_id and (real_person_position.external_id != unique_iebc_code):
                    raise Exception, "Would change the IEBC code, but it conflicted"
                real_person_position.external_id = unique_iebc_code
                maybe_save(real_person_position, **options)
            for other_position in other_position_set:
                other_person = other_position.person
                same_person = (real_person_position.person == other_person)
                if same_person:
                    removed_duplicate_position_for_same_person = True
                    # Then don't delete the other person, just delete the position:
                    if options['commit']:
                        other_position.delete()
                else:
                    # Otherwise delete both the position and the person:
                    if other_position.created < before_import_date:
                        print "!! Would be deleting a position %s (%d) created before our first import: %s" % (other_position, other_position.id, other_position.created)
                    if options['commit']:
                        other_position.delete()
                    if other_person.created < before_import_date:
                        print "!! Would be deleting a person %s (%d) created before our first import: %s" % (other_person, other_person.id, other_person.created)
                    # Create a redirect from the old slug:
                    sr = SlugRedirect(content_type=ContentType.objects.get_for_model(Person),
                                      old_object_slug=other_person.slug,
                                      new_object_id=real_person_position.person.id,
                                      new_object=real_person_position.person)
                    maybe_save(sr, **options)
                    # Then finally delete the person:
                    if options['commit']:
                        other_person.delete()


class Command(NoArgsCommand):
    help = 'Update the database with aspirants from the IEBC website'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--only-place', dest='place', help='Only remove duplicates for particular places matching this name'),
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

        cache_directory = os.path.join(data_directory, 'api-cache-2013-02-14')

        mkdir_p(cache_directory)

        for area_type in 'county', 'constituency', 'ward':
            cache_filename = os.path.join(cache_directory, area_type + '.json')
            area_type_data = get_data_with_cache(cache_filename, url('/%s/' % (area_type)))
            areas = area_type_data['region']['locations']
            for i, area in enumerate(areas):
                # Get the candidates for that area:
                code = area['code']
                candidates_cache_filename = os.path.join(cache_directory, 'candidates-for-' + area_type + '-' + code + '.json')
                candidate_data = get_data_with_cache(candidates_cache_filename, url('/candidate/', query_filter='%s=%s' % (area_type, code)))
                for race in candidate_data['candidates']:
                    place_name = race['race']
                    candidates = race['candidates']
                    if len(candidates) == 0:
                        continue
                    distinct_contest_types = set(c['contest_type'] for c in race['candidates'])
                    if len(distinct_contest_types) != 1:
                        print "Multiple contest types found for %s: %s" % (place_name, distinct_contest_types)
                    contest_type = iter(distinct_contest_types).next()
                    place_kind, session, title, race_type = known_race_type_mapping[contest_type]

                    if options['place'] and options['place'].lower() != place_name.lower():
                        continue

                    remove_duplicate_candidates_for_place(place_name,
                                                          place_kind,
                                                          session,
                                                          title,
                                                          race_type,
                                                          candidates,
                                                          **options)
