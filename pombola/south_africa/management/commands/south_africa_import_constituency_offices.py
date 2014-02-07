# This should only be used as a one-off script to import constituency
# offices from the CSV file 'all constituencies2.csv'.  This is messy
# data - columns have different formats and structures, the names of
# people don't match those in our database, places are defined
# inconsistently, etc. etc. and to represent all these relationships
# in the Pombola database schema we need to create a lot of new rows
# in different tables.  I strongly suggest this is only used for the
# initial import on the 'all_constituencies.csv', or that file with
# fixes manually applied to it.
#
# That file is in the repository at:
#
#   pombola/south_africa/data/constituencies_and_offices/all_constituencies.csv

# Things still to do and other notes:
#
#  * Save the phone numbers for individual people that are sometimes
#    come straight after their names.  (This is done for
#    administrators, but not for MPs - they may already have that
#    contact number from the original import, so that would need to be
#    checked.)
#
#  * At the moment only about 80% of the physical addresses geolocate
#    correctly. More work could be put into this, resolving them
#    manually or trying other geocoders.
#
#  * There are still various unmatched names that should be found in
#    the Pombola database.

from collections import defaultdict, namedtuple
import csv
from difflib import SequenceMatcher
from itertools import chain
import json
from optparse import make_option
import os
import re
import requests
import sys
import time
import urllib

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, CommandError
from django.db.models import Q
from django.template.defaultfilters import slugify

from pombola.core.models import (OrganisationKind, Organisation, PlaceKind,
                         ContactKind, OrganisationRelationshipKind,
                         OrganisationRelationship, Identifier, Position,
                         PositionTitle, Person)

from mapit.models import Generation, Area, Code

class LocationNotFound(Exception):
    pass

def group_in_pairs(l):
    return zip(l[0::2], l[1::2])

def fix_province_name(province_name):
    if province_name == 'Kwa-Zulu Natal':
        return 'KwaZulu-Natal'
    else:
        return province_name

def fix_municipality_name(municipality_name):
    if municipality_name == 'Merafong':
        return 'Merafong City'
    else:
        return municipality_name

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
        result = r.json()
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
            verbose(message.encode('UTF-8'))
        # FIXME: We should really check the accuracy information here, but
        # for the moment just use the 'location' coordinate as is:
        geometry = all_results[0]['geometry']
        lon = float(geometry['location']['lng'])
        lat = float(geometry['location']['lat'])
        return lon, lat, geocode_cache

def all_initial_forms(name, squash_initials=False):
    '''Generate all initialized variants of first names

    >>> for name in all_initial_forms('foo Bar baz quux', squash_initials=True):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    fB baz quux
    fBb quux

    >>> for name in all_initial_forms('foo Bar baz quux'):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    f B baz quux
    f B b quux
    '''
    names = name.split(' ')
    n = len(names)
    if n == 0:
        yield name
    for i in range(0, n):
        if i == 0:
            yield ' '.join(names)
            continue
        initials = [name[0] for name in names[:i]]
        if squash_initials:
            result = [''.join(initials)]
        else:
            result = initials
        yield ' '.join(result + names[i:])

# Build an list of tuples of (mangled_mp_name, person_object) for each
# member of the National Assembly and delegate of the National Coucil
# of Provinces:

na_member_lookup = defaultdict(set)

nonexistent_phone_number = '000 000 0000'

title_slugs = ('provincial-legislature-member',
               'committee-member',
               'alternate-member')

def warn_duplicate_name(name_form, person):
    message = "Tried to add '%s' => %s, but there were already '%s' => %s" % (
        name_form, person, name_form, na_member_lookup[name_form])
    print message

people_done = set()
for position in chain(Position.objects.filter(title__slug='member',
                                              organisation__slug='national-assembly'),
                      Position.objects.filter(title__slug='member-of-the-provincial-legislature').currently_active(),
                      Position.objects.filter(title__slug='member',
                                              organisation__kind__slug='provincial-legislature').currently_active(),
                      Position.objects.filter(title__slug__in=title_slugs).currently_active(),
                      Position.objects.filter(title__slug__startswith='minister').currently_active(),
                      Position.objects.filter(title__slug='delegate',
                                              organisation__slug='ncop').currently_active()):

    person = position.person
    if person in people_done:
        continue
    else:
        people_done.add(person)
    for name in person.all_names_set():
        name = name.lower().strip()
        # Always leave the last name, but generate all combinations of initials
        name_forms = set(chain(all_initial_forms(name),
                               all_initial_forms(name, squash_initials=True)))
        # If it looks as if there are three full names, try just
        # taking the first and last names:
        m = re.search(r'^(\S{4,})\s+\S.*\s+(\S{4,})$', name)
        if m:
            name_forms.add(u"{0} {1}".format(*m.groups()))
        for name_form in name_forms:
            if name_form in na_member_lookup:
                warn_duplicate_name(name_form, person)
            na_member_lookup[name_form].add(person)

unknown_people = set()

# Given a name string, try to find a person from the Pombola database
# that matches that as closely as possible.  Note that if the form of
# the name supplied matches more than one person, it's arbitrary which
# one you'll get back.  This doesn't happen in the South Africa data
# at the moment, but that's still a FIXME (probably by replacing this
# with PopIt's name resolution).

def find_pombola_person(name_string):

    # Strip off any phone number at the end, which sometimes include
    # NO-BREAK SPACE or a / for multiple numbers.
    name_string = re.sub(r'(?u)[\s\d/]+$', '', name_string).strip()
    # And trim any list numbers from the beginning:
    name_string = re.sub(r'^[\s\d\.]+', '', name_string)
    # Strip off some titles:
    name_string = re.sub(r'(?i)^(Min|Dep Min|Dep President|President) ', '', name_string)
    name_string = name_string.strip()
    if not name_string:
        return None
    # Move any initials to the front of the name:
    name_string = re.sub(r'^(.*?)(([A-Z] *)*)$', '\\2 \\1', name_string)
    name_string = re.sub(r'(?ms)\s+', ' ', name_string).strip().lower()
    # Score the similarity of name_string with each person:
    scored_names = []
    for actual_name, people in na_member_lookup.items():
        for person in people:
            t = (SequenceMatcher(None, name_string, actual_name).ratio(),
                 actual_name,
                 person)
            scored_names.append(t)
    scored_names.sort(reverse=True, key=lambda n: n[0])
    # If the top score is over 90%, it's very likely to be the
    # same person with the current set of MPs - this leave a
    # number of false negatives from misspellings in the CSV file,
    # though.
    if scored_names[0][0] >= 0.9:
        return scored_names[0][2]
    else:
        verbose("Failed to find a match for " + name_string.encode('utf-8'))
        return None

VERBOSE = False

def verbose(message):
    if VERBOSE:
        print message

class Command(LabelCommand):
    """Import constituency offices"""

    help = 'Import constituency office data for South Africa'

    option_list = LabelCommand.option_list + (
        make_option(
            '--test',
            action='store_true',
            dest='test',
            help='Run any doctests for this script'),
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

        if options['test']:
            import doctest
            failure_count, _ = doctest.testmod(sys.modules[__name__])
            sys.exit(0 if failure_count == 0 else 1)

        global VERBOSE
        VERBOSE = options['verbose']

        geocode_cache_filename = os.path.join(
            os.path.dirname(__file__),
            '.geocode-request-cache')

        try:
            with open(geocode_cache_filename) as fp:
                geocode_cache = json.load(fp)
        except IOError as e:
            geocode_cache = {}

        # Ensure that all the required kinds and other objects exist:

        ok_party = OrganisationKind.objects.get(slug='party')
        ok_constituency_office, _ = OrganisationKind.objects.get_or_create(
            slug='constituency-office',
            name='Constituency Office')
        ok_constituency_area, _ = OrganisationKind.objects.get_or_create(
            slug='constituency-area',
            name='Constituency Area')

        pk_constituency_office, _ = PlaceKind.objects.get_or_create(
            slug='constituency-office',
            name='Constituency Office')
        pk_constituency_area, _ = PlaceKind.objects.get_or_create(
            slug='constituency-area',
            name='Constituency Area')

        ck_address, _ = ContactKind.objects.get_or_create(
            slug='address',
            name='Address')
        ck_email, _ = ContactKind.objects.get_or_create(
            slug='email',
            name='Email')
        ck_fax, _ = ContactKind.objects.get_or_create(
            slug='fax',
            name='Fax')
        ck_telephone, _ = ContactKind.objects.get_or_create(
            slug='voice',
            name='Voice')

        pt_constituency_contact, _ = PositionTitle.objects.get_or_create(
            slug='constituency-contact',
            name='Constituency Contact')
        pt_administrator, _ = PositionTitle.objects.get_or_create(
            slug='administrator',
            name='Administrator')

        ork_has_office, _ = OrganisationRelationshipKind.objects.get_or_create(
            name='has_office')

        organisation_content_type = ContentType.objects.get_for_model(Organisation)

        contact_source = "Data from the party via Geoffrey Kilpin"

        mapit_current_generation = Generation.objects.current()

        with_physical_addresses = 0
        geolocated = 0

        created_administrators = {}

        # There's at least one duplicate row, so detect and ignore any duplicates:
        rows_already_done = set()

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
                    administrator = row['Administrator']
                    telephone = row['Tel']
                    fax = row['Fax']
                    physical_address = row['Physical Address']
                    postal_address = row['Postal Address']
                    email = row['E-mail']
                    municipality = row['Municipality']
                    wards = row['Wards']

                    abbreviated_party = party
                    m = re.search(r'\((?:|.*, )([A-Z\+]+)\)', party)
                    if m:
                        abbreviated_party = m.group(1)

                    unique_row_id = (party_code, name, party)

                    if unique_row_id in rows_already_done:
                        continue
                    else:
                        rows_already_done.add(unique_row_id)

                    # Collapse whitespace in the name to a single space:
                    name = re.sub(r'(?ms)\s+', ' ', name)

                    mz_party = Organisation.objects.get(name=party)

                    # At various points, constituency office or areas
                    # have been created with the wrong terminology, so
                    # look for any variant of the names:
                    title_data = {'party': abbreviated_party,
                                  'type': office_or_area,
                                  'party_code': party_code,
                                  'name': name}
                    possible_formats = [
                        u'{party} Constituency Area ({party_code}): {name}',
                        u'{party} Constituency Office ({party_code}): {name}',
                        u'{party} Constituency Area: {name}',
                        u'{party} Constituency Office: {name}']
                    org_slug_possibilities = [slugify(fmt.format(**title_data))
                                              for fmt in possible_formats]

                    if party_code:
                        organisation_name = u"{party} Constituency {type} ({party_code}): {name}".format(**title_data)
                    else:
                        organisation_name = u"{party} Constituency {type}: {name}".format(**title_data)

                    places_to_add = []
                    contacts_to_add = []
                    people_to_add = []
                    administrators_to_add = []

                    for contact_kind, value, in ((ck_email, email),
                                                 (ck_telephone, telephone),
                                                 (ck_fax, fax)):
                        if value:
                            contacts_to_add.append({
                                    'kind': contact_kind,
                                    'value': value,
                                    'source': contact_source})

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
                                verbose("physical_address: " + physical_address.encode('UTF-8'))
                                lon, lat, geocode_cache = geocode(physical_address, geocode_cache)
                                verbose("maps to:")
                                verbose("http://maps.google.com/maps?q=%f,%f" % (lat, lon))
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
                                verbose("XXX no results found for: " + physical_address)

                            if pobox_address is not None:
                                contacts_to_add.append({
                                        'kind': ck_address,
                                        'value': pobox_address,
                                        'source': contact_source})

                            # Deal with the different formats of MP
                            # and MPL names for different parties:
                            for representative_type in ('MP', 'MPL'):
                                if party in ('African National Congress (ANC)',
                                             'African Christian Democratic Party (ACDP)'):
                                    name_strings = re.split(r'\s{4,}',row[representative_type])
                                    for name_string in name_strings:
                                        person = find_pombola_person(name_string)
                                        if person:
                                            people_to_add.append(person)
                                elif party in ('Congress of the People (COPE)',
                                               'Freedom Front + (Vryheidsfront+, FF+)'):
                                    for contact in re.split(r'\s*;\s*', row[representative_type]):
                                        # Strip off the phone number
                                        # and email address before
                                        # resolving:
                                        person = find_pombola_person(
                                            re.sub(r'(?ms)\s*\d.*', '', contact))
                                        if person:
                                            people_to_add.append(person)
                                else:
                                    raise Exception, "Unknown party '%s'" % (party,)

                        if municipality:
                            municipality = fix_municipality_name(municipality)

                            # If there's a municipality, try to add that as a place as well:
                            mapit_municipalities = Area.objects.filter(
                                Q(type__code='LMN') | Q(type__code='DMN'),
                                generation_high__gte=mapit_current_generation,
                                generation_low__lte=mapit_current_generation,
                                name=municipality)

                            mapit_municipality = None

                            if len(mapit_municipalities) == 1:
                                mapit_municipality = mapit_municipalities[0]
                            elif len(mapit_municipalities) == 2:
                                # This is probably a Metropolitan Municipality, which due to
                                # https://github.com/mysociety/pombola/issues/695 will match
                                # an LMN and a DMN; just pick the DMN:
                                if set(m.type.code for m in mapit_municipalities) == set(('LMN', 'DMN')):
                                    mapit_municipality = [m for m in mapit_municipalities if m.type.code == 'DMN'][0]
                                else:
                                    # Special cases for 'Emalahleni' and 'Naledi', which
                                    # are in multiple provinces:
                                    if municipality == 'Emalahleni':
                                        if 'Pule' in row['MP']:
                                            mapit_municipality = Code.objects.get(type__code='l', code='MP312').area
                                        elif 'Mdaka' in row['MP']:
                                            mapit_municipality = Code.objects.get(type__code='l', code='EC136').area
                                        else:
                                            raise Exception, "Unknown Emalahleni row with MP: '{0}'".format(row['MP'])
                                    elif municipality == 'Naledi':
                                        if 'Mmusi' in row['MP']:
                                            mapit_municipality = Code.objects.get(type__code='l', code='NW392').area
                                        else:
                                            raise Exception, "Unknown Naledi row"
                                    else:
                                        raise Exception, "Ambiguous municipality name '%s'" % (municipality,)

                            if mapit_municipality:
                                place_name = u'Municipality associated with ' + organisation_name
                                places_to_add.append({
                                    'name': place_name,
                                    'slug': slugify(place_name),
                                    'kind': pk_constituency_office,
                                    'mapit_area': mapit_municipality})

                    elif office_or_area == 'Area':
                        # At the moment it's only for DA that these
                        # Constituency Areas exist, so check that assumption:
                        if party != 'Democratic Alliance (DA)':
                            raise Exception, "Unexpected party %s with Area" % (party)
                        constituency_kind = ok_constituency_area
                        province = fix_province_name(province)
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
                            for contact in re.split(r'(?ms)\s*;\s*', row[representative_type]):
                                person = find_pombola_person(contact)
                                if person:
                                    people_to_add.append(person)

                    else:
                        raise Exception, "Unknown type %s" % (office_or_area,)

                    # The Administrator column might have multiple
                    # administrator contacts, separated by
                    # semi-colons.  Each contact may have notes about
                    # them in brackets, and may be followed by more
                    # than one phone number, separated by slashes.
                    if administrator and administrator.lower() != 'vacant':
                        for administrator_contact in re.split(r'\s*;\s*', administrator):
                            # Strip out any bracketed notes:
                            administrator_contact = re.sub(r'\([^\)]*\)', '', administrator_contact)
                            # Extract any phone number at the end:
                            m = re.search(r'^([^0-9]*)([0-9\s/]*)$', administrator_contact)
                            phone_numbers = []
                            if m:
                                administrator_contact, phones = m.groups()
                                phone_numbers = [s.strip() for s in re.split(r'\s*/\s*', phones)]
                            administrator_contact = administrator_contact.strip()
                            # If there's no name after that, just skip this contact
                            if not administrator_contact:
                                continue
                            administrator_contact = re.sub(r'\s+', ' ', administrator_contact)
                            tuple_to_add = (administrator_contact,
                                            tuple(s for s in phone_numbers
                                                  if s and s != nonexistent_phone_number))
                            verbose("administrator name '%s', numbers '%s'" % tuple_to_add)
                            administrators_to_add.append(tuple_to_add)

                    organisation_kwargs = {
                        'name': organisation_name,
                        'slug': slugify(organisation_name),
                        'kind': constituency_kind}

                    # Check if this office appears to exist already:

                    identifier = None
                    identifier_scheme = "constituency-office/%s/" % (abbreviated_party,)

                    try:
                        if party_code:
                            # If there's something's in the "Party Code"
                            # column, we can check for an identifier and
                            # get the existing object reliable through that.
                            identifier = Identifier.objects.get(identifier=party_code,
                                                                scheme=identifier_scheme)
                            org = identifier.content_object
                        else:
                            # Otherwise use the slug we intend to use, and
                            # look for an existing organisation:
                            org = Organisation.objects.get(slug__in=org_slug_possibilities,
                                                           kind=constituency_kind)
                    except ObjectDoesNotExist:
                        org = Organisation()
                        if party_code:
                            identifier = Identifier(identifier=party_code,
                                                    scheme=identifier_scheme,
                                                    content_type=organisation_content_type)

                    # Make sure we set the same attributes and save:
                    for k, v in organisation_kwargs.items():
                        setattr(org, k, v)

                    if options['commit']:
                        org.save()
                        if party_code:
                            identifier.object_id = org.id
                            identifier.save()

                        # Replace all places associated with this
                        # organisation and re-add them:
                        org.place_set.all().delete()
                        for place_dict in places_to_add:
                            org.place_set.create(**place_dict)

                        # Replace all contact details associated with this
                        # organisation, and re-add them:
                        org.contacts.all().delete()
                        for contact_dict in contacts_to_add:
                            org.contacts.create(**contact_dict)

                        # Remove previous has_office relationships,
                        # between this office and any party, then re-add
                        # this one:
                        OrganisationRelationship.objects.filter(
                            organisation_b=org).delete()
                        OrganisationRelationship.objects.create(
                            organisation_a=mz_party,
                            kind=ork_has_office,
                            organisation_b=org)

                        # Remove all Membership relationships between this
                        # organisation and other people, then recreate them:
                        org.position_set.filter(title=pt_constituency_contact).delete()
                        for person in people_to_add:
                            org.position_set.create(
                                person=person,
                                title=pt_constituency_contact,
                                category='political')

                        # Remove any administrators for this organisation:
                        for position in org.position_set.filter(title=pt_administrator):
                            for contact in position.person.contacts.all():
                                contact.delete()
                            position.person.delete()
                            position.delete()
                        # And create new administrators:
                        for administrator_tuple in administrators_to_add:
                            administrator_name, phone_numbers = administrator_tuple
                            if administrator_tuple in created_administrators:
                                person = created_administrators[administrator_tuple]
                            else:
                                person = Person.objects.create(legal_name=administrator_name,
                                                               slug=slugify(administrator_name))
                                created_administrators[administrator_tuple] = person
                                for phone_number in phone_numbers:
                                    person.contacts.create(kind=ck_telephone,
                                                           value=phone_number,
                                                           source=contact_source)
                            Position.objects.create(person=person,
                                                    organisation=org,
                                                    title=pt_administrator,
                                                    category='political')

        finally:
            with open(geocode_cache_filename, "w") as fp:
                json.dump(geocode_cache, fp, indent=2)

        verbose("Geolocated %d out of %d physical addresses" % (geolocated, with_physical_addresses))
