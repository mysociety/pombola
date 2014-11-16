# This imports new and updates existing constituency offices and areas,
# and is based on south_africa_import_constituency_offices.py.

# Offices and areas are imported from a JSON file that defines the
# offices and areas and defines parties to be ignored when ending old
# (ommited) offices and areas.

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
import math

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, CommandError
from django.db.models import Q
from django.utils.text import slugify

from pombola.core.models import (OrganisationKind, Organisation, Place, PlaceKind,
                         ContactKind, Contact, OrganisationRelationshipKind,
                         OrganisationRelationship, Identifier, Position,
                         PositionTitle, Person, AlternativePersonName,
                         InformationSource)

from mapit.models import Generation, Area, Code


class LocationNotFound(Exception):
    pass

organisation_content_type = ContentType.objects.get_for_model(Organisation)

person_content_type = ContentType.objects.get_for_model(Person)

position_content_type = ContentType.objects.get_for_model(Position)

geocode_cache_filename = os.path.join(
    os.path.dirname(__file__),
    '.geocode-request-cache')

try:
    with open(geocode_cache_filename) as fp:
        geocode_cache = json.load(fp)
except IOError as e:
    geocode_cache = {}
test = 'yes'

locationsnotfound = []
personnotfound = []

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

    if address_string=='TBA':
        raise LocationNotFound

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
    try:
        message = "Tried to add '%s' => %s, but there were already '%s' => %s" % (
            name_form, person, name_form, na_member_lookup[name_form])
        print message
    except UnicodeDecodeError:
        print 'Duplicate name issue'

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


def get_mapit_municipality(municipality, province=''):
    municipality = fix_municipality_name(municipality)
    mapit_current_generation = Generation.objects.current()

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
                if province=='Mpumalanga':
                    mapit_municipality = Code.objects.get(type__code='l', code='MP312').area
                elif province=='Eastern Cape':
                    mapit_municipality = Code.objects.get(type__code='l', code='EC136').area
                else:
                    raise Exception, "Unknown Emalahleni province %s" % (province)
            elif municipality == 'Naledi':
                if province=='Northern Cape':
                    mapit_municipality = Code.objects.get(type__code='l', code='NW392').area
                else:
                    raise Exception, "Unknown Naledi province %s" % (province)
            else:
                raise Exception, "Ambiguous municipality name '%s'" % (municipality,)

def process_office(office, commit, start_date, end_date):
    global geocode_cache, locationsnotfound, personnotfound

    # Ensure that all the required kinds and other objects exist:
    ok_party = OrganisationKind.objects.get_or_create(
        slug='party',
        name='Party')
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

    constituency_kinds = {
        'area': ok_constituency_area,
        'office': ok_constituency_office
    }

    constituency_place_kinds = {
        'area': pk_constituency_area,
        'office': pk_constituency_office
    }

    ck_address, _ = ContactKind.objects.get_or_create(
        slug='address',
        name='Address')
    ck_postal_address, _ = ContactKind.objects.get_or_create(
        slug='postal_address',
        name='Postal Address')
    ck_email, _ = ContactKind.objects.get_or_create(
        slug='email',
        name='Email')
    ck_fax, _ = ContactKind.objects.get_or_create(
        slug='fax',
        name='Fax')
    ck_telephone, _ = ContactKind.objects.get_or_create(
        slug='voice',
        name='Voice')

    ork_has_office, _ = OrganisationRelationshipKind.objects.get_or_create(
        name='has_office'
    )

    pt_constituency_contact, _ = PositionTitle.objects.get_or_create(
        slug='constituency-contact',
        name='Constituency Contact')
    pt_administrator, _ = PositionTitle.objects.get_or_create(
        slug='administrator',
        name='Administrator')
    pt_administrator_volunteer, _ = PositionTitle.objects.get_or_create(
        slug='administrator-volunteer',
        name='Administrator (volunteer)')
    pt_volunteer, _ = PositionTitle.objects.get_or_create(
        slug='volunteer',
        name='Volunteer')
    pt_coordinator, _ = PositionTitle.objects.get_or_create(
        slug='coordinator',
        name='Coordinator')
    pt_community_development_field_worker, _ = PositionTitle.objects.get_or_create(
        slug='community-development-field-worker',
        name='Community Development Field Worker')

    position_titles = {
        'Constituency Contact': pt_constituency_contact,
        'Administrator': pt_administrator,
        'Administrator (volunteer)': pt_administrator_volunteer,
        'Volunteer': pt_volunteer,
        'Coordinator': pt_coordinator,
        'Community Development Field Worker': pt_community_development_field_worker}

    ork_has_office, _ = OrganisationRelationshipKind.objects.get_or_create(
        name='has_office')

    contact_kinds = {
        'E-mail': ck_email,
        'Tel': ck_telephone,
        'Fax': ck_fax,
        'Physical Address': ck_address,
        'Postal Address': ck_postal_address
    }

    print "\n", office['Title']

    infosources = []
    if 'Sources' in office:
        source_url = office['Sources'][0]['Source URL']
        first = True
        for source in office['Sources']:
            print 'Adding InformationSource %s (%s)' % (
                office['Sources'][0]['Source URL'],
                office['Sources'][0]['Source Note']
            )

            infosources.append({
                'source_url': source['Source URL'],
                'source_note': source['Source Note']
            })

            if first:
                first = False
                continue

            source_url += ' and ' + source['Source URL']
    else:
        source_url = office['Source URL']
        source_note = office['Source Note']
        infosources.append({
            'source_url': office['Source URL'],
            'source_note': office['Source Note']
        })
        print 'Adding InformationSource %s (%s)' % (
            office['Source URL'],
            office['Source Note']
        )

    if ('Physical Address' in office) and (not 'South Africa' in office['Physical Address']) and (office['Physical Address']!='TBA'):
        office['Physical Address'] = office['Physical Address'] + ', South Africa'

    if ('Location' in office) and (office['Location']!='TBA') and (not office['Province'].lower() in office['Location'].lower()):
        office['Location'] = office['Location'] + ', ' + office['Province'] + ', South Africa'

    if ('Location' in office) and (not 'South Africa' in office['Location']) and (office['Location']!='TBA'):
        office['Location'] = office['Location'] + ', South Africa'

    #first determine whether the office already exists
    organisation = None
    try:
        organisation = Organisation.objects.get(
            name=office['Title']
        )
    except ObjectDoesNotExist:
        #check identifiers
        try:
            if 'identifiers' in office:
                for identifier_scheme, party_code in office['identifiers'].items():
                    identifier = Identifier.objects.get(
                        identifier=party_code,
                        scheme=identifier_scheme)
                    organisation = identifier.content_object
        except ObjectDoesNotExist:
            pass

    if organisation:  #existing office
        if organisation.name != office['Title']:
            print 'Changing name from %s to %s' % (organisation.name, office['Title'])

            if commit:
                organisation.name = office['Title']
                organisation.save()

        if organisation.ended != 'future':
            print 'Changing ended date from %s to future' % (organisation.ended)

            if commit:
                organisation.ended = 'future'
                organisation.save()

    else:
        print 'Creating new %s' % (office['Type'])

        if commit:
            organisation = Organisation.objects.create(
                name=office['Title'],
                slug=slugify(office['Title']),
                kind=constituency_kinds[office['Type']],
                started=start_date,
                ended='future')

    #information source
    if commit:
        for infosource in infosources:
            InformationSource.objects.get_or_create(
                source = infosource['source_url'],
                note = infosource['source_note'],
                entered = True,
                content_type=organisation_content_type,
                object_id=organisation.id
            )

    #relationship to party
    try:
        party = Organisation.objects.get(slug=office['Party'].lower())

        organisation_relationships = OrganisationRelationship.objects.get(
            organisation_a=party,
            organisation_b=organisation,
            kind=ork_has_office
        )

        #if the relationship exists nothing needs to change
        print 'Retaining relationship with %s' % (party)

    except ObjectDoesNotExist, AttributeError:
        print 'Adding relationship with %s' % (party)

        if commit:
            OrganisationRelationship.objects.create(
                organisation_a=party,
                organisation_b=organisation,
                kind=ork_has_office
            )

    office_fields = [
        'E-mail',
        'Tel',
        'Fax',
        'Physical Address',
        'Postal Address'
    ]

    for field in office_fields:
        if field in office:
            try:
                if not organisation:
                    raise ObjectDoesNotExist

                contact = Contact.objects.get(
                    object_id=organisation.id,
                    content_type=organisation_content_type,
                    kind=contact_kinds[field])
                if office[field] != contact.value:
                    print 'Changing %s from %s to %s' % (field, contact.value, office[field])

                    if commit:
                        contact.value = office[field]
                        contact.save()

                print 'Updating contact source to %s' % (source_url)
                if commit:
                    contact.source = source_url
                    contact.save()

            except ObjectDoesNotExist:
                print 'Creating new contact (%s: %s)' % (field, office[field])

                if commit:
                    Contact.objects.create(
                        object_id=organisation.id,
                        content_type=organisation_content_type,
                        kind=contact_kinds[field],
                        value=office[field],
                        source=source_url)

        else:
            try:
                if not organisation:
                    raise ObjectDoesNotExist

                contact = Contact.objects.get(
                    object_id=organisation.id,
                    content_type=organisation_content_type,
                    kind=contact_kinds[field])
                print 'Deleting', contact

                if commit:
                    contact.delete()

            except ObjectDoesNotExist:
                pass

    if 'Municipality' in office:
        mapit_municipality = get_mapit_municipality(office['Municipality'], office.get('Province', ''))

        if mapit_municipality:
            place_name = u'Municipality associated with ' + office['Title']
            try:
                if not organisation:
                    raise ObjectDoesNotExist

                place = Place.objects.get(
                    name__startswith=u'Municipality associated with ',
                    organisation=organisation)

                if place.name != place_name:
                    'Changing municipality association name from %s to %s' % (place.name, place_name)

                    if commit:
                        place.name = place_name
                        place.save()

                if place.mapit_area != mapit_municipality:
                    print 'Changing municipality mapit association from %s to %s' % (place.mapit_area, mapit_municipality)

                    if commit:
                        place.mapit_area = mapit_municipality
                        place.save()

            except ObjectDoesNotExist:
                print 'Create municipality association'
                to_add = {
                    'name': place_name,
                    'slug': slugify(place_name),
                    'kind': constituency_place_kinds[office['Type']],
                    'mapit_area': mapit_municipality,}
                print to_add

                if commit:
                    place_to_add = Place.create(
                        name=to_add.name,
                        slug=to_add.slug,
                        kind=to_add.kind,
                        mapit_area=to_add.mapit_area,
                        organisation=organisation)

    if 'manual_lonlat' in office or 'Physical Address' in office or 'Location' in office:
        reference_location = ''
        try:
            if 'manual_lonlat' in office:
                #FIXME implement
                print 'manual'
            elif 'Location' in office:
                reference_location = office['Location']
                lon, lat, geocode_cache = geocode(office['Location'], geocode_cache)
            elif 'Physical Address' in office:
                reference_location = office['Physical Address']
                #geocode physical address
                lon, lat, geocode_cache = geocode(office['Physical Address'], geocode_cache)

            location = Point(lon, lat)
            if office['Type']=='area':
                name = u'Unknown sub-area of %s known as %s' % (office['Province'], office['Title'])
            else:
                name = u'Approximate position of ' + office['Title']

            try:
                if not organisation:
                    raise ObjectDoesNotExist

                if office['Type'] == 'area':
                    place = Place.objects.get(
                        name__startswith=u'Unknown sub-area of',
                        organisation=organisation)

                else:
                    place = Place.objects.get(
                        name__startswith=u'Approximate position of ',
                        organisation=organisation)

                if place.location != location:
                    print 'Changing location from %s to %s' % (place.location, location)

                    #calculate the distance between the points to
                    #simplify determining whether the cause is a minor
                    #geocode change using the haversine formula
                    #http://www.movable-type.co.uk/scripts/latlong.html
                    r = 6371
                    lat1 = math.radians(place.location.y)
                    lat2 = math.radians(location.y)
                    delta_lat = math.radians(location.y-place.location.y)
                    delta_lon = math.radians(location.x-place.location.x)

                    a = math.sin(delta_lat/2)**2 + \
                        math.cos(lat1) * math.cos(lat2) * \
                        math.sin(delta_lon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));

                    d = r * c;

                    print "%s km https://www.google.com/maps/dir/'%s,%s'/'%s,%s'/" % (d, place.location.y, place.location.x, location.y, location.x)

                    if commit:
                        place.location = location
                        place.save()

                if place.name != name:
                    print 'Changing location name from %s to %s' % (place.name, name)

                    if commit:
                        place.name = name
                        place.save()

            except ObjectDoesNotExist:
                print 'Create constituency location'

                if commit:
                    Place.objects.create(
                        name=name,
                        slug=slugify(name),
                        organisation=organisation,
                        location=location,
                        kind=constituency_place_kinds[office['Type']])

        except LocationNotFound:
            locationsnotfound.append([office['Title'], reference_location])
            print "XXX no results found for: " + reference_location

    else:
        print 'No office/area location specified'

    people_to_keep = []
    if 'People' in office:
        for person in office['People']:
            #person matching needs to be improved - for now attempt
            #find_pombola_person (from
            #south_africa_import_constituency_offices command) otherwise
            #direct match.
            pombola_person = find_pombola_person(person['Name'])
            if not pombola_person:
                #use filter().distinct() instead of get due to multiple
                #rows being returned
                pombola_person = Person.objects.filter(
                    Q(legal_name=person['Name']) |
                    Q(alternative_names__alternative_name=person['Name'])).distinct()
                if len(pombola_person)==0:
                    pombola_person = None
                else:
                    pombola_person = pombola_person[0]

            #check person currently holds office
            accept_person = True
            if pombola_person and person['Position']=='Constituency Contact':
                position_check = Position.objects.filter(
                    person=pombola_person,
                    organisation__kind__slug__in=['parliament', 'provincial-legislature'])
                if len(position_check)==0:
                    accept_person=False
                    print '%s is not an MP or MPL' % (pombola_person.name)

            if pombola_person and accept_person:
                #check if the position already exists
                positions = Position.objects.filter(
                    person=pombola_person,
                    organisation=organisation,
                    title=position_titles[person['Position']]
                    ).currently_active()

                if not positions:
                    print 'Creating position (%s) for %s' % (person['Position'], pombola_person)

                    if commit:
                        positiontitle, _ = PositionTitle.objects.get_or_create(
                            name=person['Position'])

                        position = Position.objects.create(
                            person=pombola_person,
                            organisation=organisation,
                            title=positiontitle,
                            start_date=start_date,
                            end_date='future')

                        people_to_keep.append(position.id)

                        #information source
                        for infosource in infosources:
                            InformationSource.objects.get_or_create(
                                source = infosource['source_url'],
                                note = infosource['source_note'],
                                entered = True,
                                content_type=position_content_type,
                                object_id=position.id
                            )

                for position in positions:
                    people_to_keep.append(position.id)
                    print 'Retaining %s' % (position)

                #check cell number
                if 'Cell' in person:
                    contacts = Contact.objects.filter(
                        object_id=pombola_person.id,
                        content_type=person_content_type,
                        kind=ck_telephone)

                    #if only one cell exists replace
                    if len(contacts)==1:
                        print 'Updating tel number for', pombola_person, 'from', contacts[0].value, 'to', person['Cell']

                        if commit:
                            contacts[0].value = person['Cell']
                            contacts[0].save()
                    else:
                        #otherwise check if the cell
                        #has already been loaded
                        add = True
                        #check if already exists
                        for contact in contacts:
                            existing = re.sub('[^0-9]', '', contact.value)
                            new = re.sub('[^0-9]', '', person['Cell'])
                            if existing==new:
                                add = False

                        if add:
                            print pombola_person
                            print person['Cell']
                            print 'Adding tel number for', pombola_person, '-', person['Cell']

                            if commit:
                                Contact.objects.create(
                                    object_id=pombola_person.id,
                                    content_type=person_content_type,
                                    kind=ck_telephone,
                                    value=person['Cell'],
                                    source=source_url)

                    print 'Updating contact source to %s' % (source_url)

                    if commit:
                        for contact in contacts:
                            contact.source = source_url
                            contact.save()

                #check email
                if 'Email' in person:
                    contacts = Contact.objects.filter(
                        object_id=pombola_person.id,
                        content_type=person_content_type,
                        kind=ck_email)

                    #if only one email exists replace
                    if len(contacts)==1:
                        print 'Updating email for %s from %s to %s' % (pombola_person, contacts[0].value, person['Email'])

                        if commit:
                            contacts[0].value = person['Email']
                            contacts[0].save()
                    else:
                        #otherwise check if the email has already been
                        #loaded
                        add = True
                        #check if already exists
                        for contact in contacts:
                            existing = contact.value
                            new = person['Email']
                            if existing==new:
                                add = False

                        if add:
                            print 'Adding email for %s: %s' % (pombola_person, person['Email'])

                            if commit:
                                Contact.objects.create(
                                    object_id=pombola_person.id,
                                    content_type=person_content_type,
                                    kind=ck_email,
                                    value=person['Email'],
                                    source=source_url)

                    print 'Updating contact source to %s' % (source_url)

                    if commit:
                        for contact in contacts:
                            contact.source = source_url
                            contact.save()

                #check alternative name
                if 'Alternative Name' in person:
                    try:
                        alternative_name = AlternativePersonName.objects.get(
                            person=pombola_person,
                            alternative_name=person['Alternative Name'])
                    except ObjectDoesNotExist:
                        print 'Adding alternative name for %s: %s' % (pombola_person, person['Alternative Name'].encode('utf-8'))

                        if commit:
                            AlternativePersonName.objects.create(
                                person=pombola_person,
                                alternative_name=person['Alternative Name'])

            if not pombola_person:
                if person['Position'] == 'Constituency Contact':
                    personnotfound.append([office['Title'], person['Name']])
                    print 'Failed to match representative', person['Name']
                else:
                    print 'Creating person (%s) with position (%s)' % (person['Name'], person['Position'])

                    if commit:
                        create_person = Person.objects.create(
                            legal_name=person['Name'],
                            slug=slugify(person['Name']))

                        Position.objects.create(
                            person=create_person,
                            organisation=organisation,
                            title=position_titles[person['Position']],
                            start_date=start_date,
                            end_date='future')

                    if 'Cell' in person:
                        print 'Adding cell number %s' % (person['Cell'])

                        if commit:
                            Contact.objects.create(
                                object_id=create_person.id,
                                content_type=person_content_type,
                                kind=ck_telephone,
                                value=person['Cell'],
                                source=source_url)

                    if 'Alternative Name' in person:
                        print 'Adding alternative name %s' % (unicode(person['Alternative Name'], 'utf-8'))

                        if commit:
                            AlternativePersonName.objects.create(
                                person=create_person,
                                alternative_name=person['Alternative Name'])

    #find the positions to end
    if organisation:
        positions = Position.objects.filter(
            organisation=organisation
            ).exclude(id__in=people_to_keep).currently_active()

        for position in positions:
            print 'Ending %s' % (position)

            if commit:
                position.end_date = end_date
                position.save()

    #FIXME: check summary, kind, started, ended,
    #identifiers (not expected at present)

    if organisation:
        return organisation


class Command(LabelCommand):
    """Update constituency offices"""

    help = 'Update constituency office data for South Africa'

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

        commit = False
        if options['commit']:
            commit = True

        global VERBOSE
        VERBOSE = options['verbose']

        contact_source_2013 = "Data from the party (2013)"

        organisations_to_keep = []

        try:
            with open(input_filename) as fp:
                data = json.load(fp)

                for office in data['offices']:
                    organisation = process_office(office, commit, data['start_date'], data['end_date'])

                    if organisation:
                        organisations_to_keep.append(organisation.id)

        finally:
            with open(geocode_cache_filename, "w") as fp:
                json.dump(geocode_cache, fp, indent=2)

        #find the organisations to end
        organisations_to_end = Organisation.objects.filter(
            kind__slug__in=['constituency-area', 'constituency-office']).exclude(
            id__in=organisations_to_keep)

        print "\nNot ending offices starting with:"
        for exclude in data['exclude']:
            print exclude
            organisations_to_end = organisations_to_end.exclude(name__startswith=exclude)

        print "\nOffices to end"
        for organisation in organisations_to_end:
            if organisation.is_ongoing():
                print 'Ending %s' % (organisation)

                if commit:
                    organisation.ended = data['end_date']
                    organisation.save()

                positions = Position.objects.filter(organisation=organisation).currently_active()

                for position in positions:
                    print 'Ending %s' % (position)

                    if commit:
                        position.end_date = data['end_date']
                        position.save()

        contacts_correct = Contact.objects.filter(source='Data from the party via Geoffrey Kilpin')

        if contacts_correct:
            print "\nCorrecting contact sources"

            for contact in contacts_correct:
                try:
                    print 'Changing source for %s from %s to %s' % (contact, contact.source, contact_source_2013)
                except UnicodeDecodeError:
                    print 'Changing contact source'

                if commit:
                    contact.source = contact_source_2013
                    contact.save()

        #print people and locations not found for checking
        print 'People not found'
        for person in personnotfound:
            print person[0], "\t", person[1]

        print 'Locations not found'
        for location in locationsnotfound:
            print location[0], "\t", location[1]
            print ''
