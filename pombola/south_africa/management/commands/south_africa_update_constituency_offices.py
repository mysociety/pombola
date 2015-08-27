# This imports new and updates existing constituency offices and areas,
# and is based on south_africa_import_constituency_offices.py.

# Offices and areas are imported from a JSON file that defines the
# offices and areas and defines parties to be ignored when ending old
# (omitted) offices and areas.

import json
from optparse import make_option
import re

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand
from django.db.models import Q
from django.utils.text import slugify

from popolo.models import ContactDetail, Identifier, Source

from pombola.core.models import (OrganisationKind, PopoloOrganization, Place, PlaceKind,
                         OrganisationRelationshipKind,
                         OrganisationRelationship, PopoloMembership,
                         PositionTitle, PopoloPerson, PopoloPersonOtherName
                                 )

from ..helpers import (
    LocationNotFound,
    geocode, get_na_member_lookup, get_mapit_municipality, find_pombola_person,
    get_geocode_cache, write_geocode_cache, debug_location_change
)

organisation_content_type = ContentType.objects.get_for_model(PopoloOrganization)

person_content_type = ContentType.objects.get_for_model(PopoloPerson)

position_content_type = ContentType.objects.get_for_model(PopoloMembership)

test = 'yes'

locationsnotfound = []
personnotfound = []

nonexistent_phone_number = '000 000 0000'

VERBOSE = False

def process_office(office, commit, start_date, end_date, na_member_lookup, geocode_cache):
    global locationsnotfound, personnotfound

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
                source['Source URL'],
                source['Source Note']
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
            'source_url': source_url,
            'source_note': source_note
        })
        print 'Adding InformationSource %s (%s)' % (source_url, source_note)


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

        OrganisationRelationship.objects.get(
            organisation_a=party,
            organisation_b=organisation,
            kind=ork_has_office
        )

        #if the relationship exists nothing needs to change
        print 'Retaining relationship with %s' % (party)

    except (ObjectDoesNotExist, AttributeError):
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
                    Place.objects.create(
                        name=to_add['name'],
                        slug=to_add['slug'],
                        kind=to_add['kind'],
                        mapit_area=to_add['mapit_area'],
                        organisation=organisation)

    if 'manual_lonlat' in office or 'Physical Address' in office or 'Location' in office:
        reference_location = ''
        try:
            if 'manual_lonlat' in office:
                #FIXME implement
                print 'manual'
            elif 'Location' in office:
                reference_location = office['Location']
                lon, lat, geocode_cache = geocode(office['Location'], geocode_cache, VERBOSE)
            elif 'Physical Address' in office:
                reference_location = office['Physical Address']
                #geocode physical address
                lon, lat, geocode_cache = geocode(office['Physical Address'], geocode_cache, VERBOSE)

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

                    debug_location_change(place.location, location)

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
            pombola_person = find_pombola_person(person['Name'], na_member_lookup, VERBOSE)
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
                        AlternativePersonName.objects.get(
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

        na_member_lookup = get_na_member_lookup()
        geocode_cache = get_geocode_cache()

        try:
            with open(input_filename) as fp:
                data = json.load(fp)

                for office in data['offices']:
                    organisation = process_office(
                        office,
                        commit,
                        data['start_date'],
                        data['end_date'],
                        na_member_lookup,
                        geocode_cache
                    )

                    if organisation:
                        organisations_to_keep.append(organisation.id)

        finally:
            write_geocode_cache(geocode_cache)

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
