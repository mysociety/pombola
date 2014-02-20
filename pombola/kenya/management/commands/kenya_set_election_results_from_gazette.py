# A script to set the correct Ward Representative and Governor for
# each place, using the data from the Kenya Gazette.  This calls
# core_create_elected_positions once the correct aspirant has been
# found.

from collections import namedtuple
import csv
import difflib
import os
import re
import sys

from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand, CommandError
from django.template.defaultfilters import slugify

from pombola.core.models import (
    AlternativePersonName, Organisation, Person, Place, PlaceKind, Position,
    PositionTitle)

data_directory = os.path.join(sys.path[0], 'pombola', 'kenya', '2013-election-data')
gazette_directory = os.path.join(data_directory, 'gazette-results')

place_name_corrections = {}

with open(os.path.join(data_directory, 'wards-names-matched.csv')) as fp:
    reader = csv.reader(fp)
    for api_name, db_name in reader:
        if api_name and db_name:
            place_name_corrections[api_name] = db_name


def mangle_place_name(place_name):
    """Downcase and remove all non-whitespace characters from a place name"""
    place_name = re.sub(r'\W', '', place_name)
    return place_name.lower()


def get_person_by_any_name(name):
    """Find a person from any of their alternative names"""
    results = list(Person.objects.filter(legal_name__iexact=name))
    if len(results) == 0:
        results += list(AlternativePersonName.objects.filter(
            alternative_name__iexact=name))
    return results


def get_matching_person_from_aspirants(winner_full_name, aspirants):
    """Find the aspirant who matches the given name"""
    matching_place_aspirants = [wa for wa in aspirants
                               if wa.name == winner_full_name]

    if len(matching_place_aspirants) == 0:

        # In that case try to find the person otherwise:
        matching_people = get_person_by_any_name(winner_full_name)

        if len(matching_people) == 0:
            # Use difflib to find the closest fuzzy match out of the aspirants:
            fuzzy_matches = [(o,
                              difflib.SequenceMatcher(None, winner_full_name, o.legal_name))
                             for o in aspirants]
            best_match = max(fuzzy_matches, key=lambda x: x[1].ratio())
            print "  best fuzzy match was:", best_match[0].legal_name
            print "      to the gazette's:", winner_full_name
            return (True, best_match[0])
        elif len(matching_people) == 1:
            return (False, matching_people[0])
        elif len(matching_people) >= 1:
            print "  Multiple matching aspirants found:"
            for matching_person in matching_people:
                print "    ", matching_person
            raise Exception, "Multiple matching aspirants from alternative names found"

    elif len(matching_place_aspirants) == 1:
        return (False, matching_place_aspirants[0])

    elif len(matching_place_aspirants) > 1:
        print "  Multiple matching aspirants found:"
        for wa in matching_place_aspirants:
            print "    " + str(wa)
        raise Exception, "Multiple matching aspirants from main name found"

PositionData = namedtuple('PositionData',
                          ['placekind',
                           'csv_filename',
                           'place_name_column',
                           'slugify_place_name',
                           'position_title',
                           'aspirant_position_title',
                           'row_to_name'])

try:
    ward_representative_position_data = PositionData(
        placekind=PlaceKind.objects.get(name='Ward'),
        csv_filename=os.path.join(gazette_directory, 'ward-results.csv'),
        place_name_column='Ward Name',
        slugify_place_name=lambda pn: 'ward-' + slugify(pn),
        position_title=PositionTitle.objects.get_or_create(
                name='Ward Representative',
                slug='ward-representative',
                requires_place=True)[0],
        aspirant_position_title=PositionTitle.objects.get(name='Aspirant Ward Representative'),
        row_to_name=lambda row: row['Full Names A'] + ' ' + row['Full Names B'])

    governor_position_data = PositionData(
        placekind=PlaceKind.objects.get(name='County'),
        csv_filename=os.path.join(gazette_directory, 'governors-results.csv'),
        place_name_column='County',
        slugify_place_name=lambda pn: slugify(pn) + '-county',
        position_title=PositionTitle.objects.get(name='Governor'),
        aspirant_position_title=PositionTitle.objects.get(name='Aspirant Governor'),
        row_to_name=lambda row: row['Governor'])

except (PlaceKind.DoesNotExist, PositionTitle.DoesNotExist):
    # This should only happen if this isn't a Kenya database, but this
    # file will be imported when running tests when you might have the
    # database for any country.  FIXME: switch this to be a function
    # that returns the mapping; this is just a temporary workaround
    # since we're not sure this script will ever be used again, so
    # it's not worth the time to test a better fix.
    ward_representative_position_data = None
    governor_position_data = None

class Command(NoArgsCommand):
    help = 'Set the elected ward representatives and governors'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        republic_organisation = Organisation.objects.get(name='REPUBLIC OF KENYA')

        for pd in (governor_position_data,
                   ward_representative_position_data):

            mangled_place_names = dict((mangle_place_name(p.name), p) for p in
                                       Place.objects.filter(kind=pd.placekind))

            with open(pd.csv_filename) as f:
                for row in csv.DictReader(f):

                    # Find the place from the name in the gazette:
                    print "==========="
                    place_name = row[pd.place_name_column]
                    place_name = place_name_corrections.get(place_name.upper(), place_name)
                    place_name = re.sub(r'(\w) *([/-]) *(\w)', '\\1 \\2 \\3', place_name)
                    if not(place_name):
                        continue
                    place_name_slugified = pd.slugify_place_name(place_name)
                    place_name_mangled = mangle_place_name(place_name)
                    try:
                        place = Place.objects.get(slug=place_name_slugified)
                        print place.name.encode('utf-8')
                    except Place.DoesNotExist:
                        place = mangled_place_names.get(place_name_mangled)
                        if place:
                            print place.name.encode('utf-8')
                        else:
                            print "missing", place_name, place_name_slugified
                            continue

                    # Some wards have their results still postponed,
                    # so ignore those - at the moment those are:
                    #
                    #    Angata Nanyokie
                    #    Gokeharaka/Geta mbwega
                    #    Nyabasi West
                    #
                    # Just ignore them until there's a result:
                    if row.get('Full Names A', '') == '(Postponed)':
                        continue

                    winner_full_name = pd.row_to_name(row)
                    print "+" + winner_full_name

                    all_aspirants = place.get_aspirants() or []

                    # If there is already a current holder of that
                    # position, someone's already set the winner:
                    current_holder = None
                    try:
                        current_holder = place.position_set.all().current_politician_positions().get(title__name=pd.position_title).person
                        matching_people = get_person_by_any_name(winner_full_name)
                        if not matching_people:
                            print "  There already is a current %s for %s who didn't match:" % (pd.position_title,
                                                                                 place)
                            print "    current_holder.person.name:", current_holder.name
                            print "                  gazette name:", winner_full_name
                            print "  So adding '%s' as an alternative name for %s" % (winner_full_name, current_holder)
                            # Note that for all the cases in the
                            # database at the time of writing these
                            # are correct synomyms, but they have to
                            # be checked by hand:
                            if options['commit']:
                                current_holder.add_alternative_name(winner_full_name)
                    except Position.DoesNotExist:
                        pass

                    if not (current_holder or all_aspirants):
                        print "### There was no current holder of the position and no aspirants"
                        continue

                    aspirants_for_place_tuples = [t for t in all_aspirants if t[0] == place]
                    if len(aspirants_for_place_tuples) > 1:
                        raise Exception, "Multiple identical places returned by get_aspirants()"

                    winner_found_in_aspirants = None
                    if aspirants_for_place_tuples:

                        aspirant_position_to_people = aspirants_for_place_tuples[0][1]

                        place_aspirants = aspirant_position_to_people.get(pd.aspirant_position_title.name)
                        if place_aspirants:
                            matched_fuzzily, winner_found_in_aspirants = get_matching_person_from_aspirants(winner_full_name, place_aspirants)

                    # Now we have either current_holder or winner_found_in_aspirants
                    if current_holder and winner_found_in_aspirants and (current_holder != winner_found_in_aspirants):
                        print "  Found both a current holder, and a winner in the aspirants, but they weren't the same:"
                        print "               current_holder:", current_holder
                        print "    winner_found_in_aspirants:", winner_found_in_aspirants
                        raise Exception, "Inconsistent winners found"

                    if not (current_holder or winner_found_in_aspirants):
                        print "  Found neither a current_holder nor a winner_found_in_aspirants"
                        raise Exception, "Found no winner"

                    winner = current_holder or winner_found_in_aspirants

                    # Copy the existing options, so we pass on 'commit' and 'verbosity':
                    command_options = options.copy()
                    command_options['place'] = place.slug
                    command_options['elected_organisation'] = republic_organisation.slug
                    command_options['aspirant_title'] = pd.aspirant_position_title.slug
                    command_options['aspirant_end_date'] = '2013-03-04'
                    command_options['elected_person'] = winner.slug
                    command_options['elected_title'] = pd.position_title.slug
                    command_options['elected_subtitle'] = None
                    command_options['elected_start_date'] = '2013-03-10'

                    call_command('core_create_elected_positions',
                                 **command_options)
