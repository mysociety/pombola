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

import csv
from optparse import make_option
import re
import sys

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand
from django.utils.text import slugify

from mapit.models import Area, Generation

from pombola.core.models import (OrganisationKind, PopoloOrganization, PlaceKind,
                         OrganisationRelationshipKind,
                         OrganisationRelationship, PopoloMembership,
                         PositionTitle, PopoloPerson)

from ..helpers import (
    fix_province_name, LocationNotFound,
    geocode, get_na_member_lookup, find_pombola_person, get_mapit_municipality,
    get_geocode_cache, write_geocode_cache
)

# Build an list of tuples of (mangled_mp_name, person_object) for each
# member of the National Assembly and delegate of the National Coucil
# of Provinces:

nonexistent_phone_number = '000 000 0000'

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

        geocode_cache = get_geocode_cache()

        na_member_lookup = get_na_member_lookup()

        # Ensure that all the required kinds and other objects exist:

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
                    manual_lonlat = row['Manually Geocoded LonLat']
                    province = row['Province']
                    office_or_area = row['Type']
                    party = row['Party']
                    administrator = row['Administrator']
                    telephone = row['Tel']
                    fax = row['Fax']
                    physical_address = row['Physical Address']
                    email = row['E-mail']
                    municipality = row['Municipality']

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
                                if manual_lonlat:
                                    verbose("using manually specified location: " + manual_lonlat)
                                    lon, lat = map(float, manual_lonlat.split(","))
                                else:
                                    lon, lat, geocode_cache = geocode(physical_address, geocode_cache, VERBOSE)
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
                                             "African Peoples' Convention (APC)",
                                             "Azanian People's Organisation (AZAPO)",
                                             'Minority Front (MF)',
                                             'United Christian Democratic Party (UCDP)',
                                             'United Democratic Movement (UDM)',
                                             'African Christian Democratic Party (ACDP)'):
                                    name_strings = re.split(r'\s{4,}',row[representative_type])
                                    for name_string in name_strings:
                                        person = find_pombola_person(name_string, na_member_lookup, VERBOSE)
                                        if person:
                                            people_to_add.append(person)
                                elif party in ('Congress of the People (COPE)',
                                               'Freedom Front + (Vryheidsfront+, FF+)'):
                                    for contact in re.split(r'\s*;\s*', row[representative_type]):
                                        # Strip off the phone number
                                        # and email address before
                                        # resolving:
                                        person = find_pombola_person(
                                            re.sub(r'(?ms)\s*\d.*', '', contact),
                                            na_member_lookup,
                                            VERBOSE
                                        )
                                        if person:
                                            people_to_add.append(person)
                                else:
                                    raise Exception, "Unknown party '%s'" % (party,)

                        if municipality:
                            mapit_municipality = get_mapit_municipality(
                                municipality, province
                            )

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
                                person = find_pombola_person(contact, na_member_lookup, VERBOSE)
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
            write_geocode_cache(geocode_cache)

        verbose("Geolocated %d out of %d physical addresses" % (geolocated, with_physical_addresses))
