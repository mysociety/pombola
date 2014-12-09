import sys
import slumber
import json
import datetime
from collections import defaultdict
from urlparse import urljoin

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person, Organisation, Position
from pombola import country

extra_popolo_person_fields = (
    'email',
    'summary',
    'biography',
    'national_identity',
    'family_name',
    'given_name',
    'additional_name',
    'honorific_prefix',
    'honorific_suffix',
    'sort_name',
    'gender',
)

def date_to_partial_iso8601(approx_date):
    """Get a (possibly partial) ISO 8601 representation of an ApproximateDate

    >>> date_to_partial_iso8601(ApproximateDate(2012, 6, 2))
    '2012-06-02'
    >>> date_to_partial_iso8601(ApproximateDate(2010))
    '2010'
    >>> date_to_partial_iso8601(ApproximateDate(2012, 2))
    '2012-02'
    """
    year = approx_date.year
    month = approx_date.month
    day = approx_date.day
    if year and month and day:
        d = datetime.date(year, month, day)
        return d.strftime("%Y-%m-%d")
    elif year and month and not day:
        d = datetime.date(year, month, 1)
        return d.strftime("%Y-%m")
    elif year and not month and not day:
        d = datetime.date(year, 1, 1)
        return d.strftime("%Y")

def add_identifiers_to_properties(o, properties, primary_id_scheme):
    properties['id'] = o.get_popolo_id(primary_id_scheme)
    secondary_identifiers = []
    for scheme, identifiers in o.get_all_identifiers().items():
        sorted_identifiers = sorted(identifiers)
        secondary_identifiers.append({
            'scheme': scheme,
            'identifier': sorted_identifiers[0]
        })
    properties['identifiers'] = secondary_identifiers

def add_contact_details_to_properties(o, properties):
    contacts = []
    for c in o.contacts.all():
        if not c.value:
            continue
        contact = {
            'type': c.kind.slug,
            'value': c.value}
        if c.note:
            contact['note'] = c.note
        contacts.append(contact)
    properties['contact_details'] = contacts

def add_start_and_end_date(o, properties, start_key_map=None, end_key_map=None):
    if start_key_map is None:
        start_key_map = ('start_date', 'start_date')
    if end_key_map is None:
        end_key_map = ('end_date', 'end_date')
    start_value = getattr(o, start_key_map[0])
    end_value = getattr(o, end_key_map[0])
    if start_value and not start_value.past:
        properties[start_key_map[1]] = date_to_partial_iso8601(start_value)
    if end_value and not end_value.future:
        properties[end_key_map[1]] = date_to_partial_iso8601(end_value)

def add_other_names(person, properties):
    properties['other_names'] = []
    for an in person.alternative_names.all():
        an_properties = {'name': an.alternative_name}
        add_start_and_end_date(an, an_properties)
        if an.note:
            an_properties['note'] = an.note
        properties['other_names'].append(an_properties)

def get_organizations(primary_id_scheme, base_url):
    """Return a list of Popolo organization objects"""

    result = []

    oslug_to_categories = defaultdict(set)

    for pos in Position.objects.all():
        if pos.organisation:
            slug = pos.organisation.slug
            oslug_to_categories[slug].add(pos.category)

    all_categories = set()
    oslug_to_category = {}

    oslug_to_categories['university-of-nairobi'] = set([u'education'])
    oslug_to_categories['kenyatta-university'] = set([u'education'])
    oslug_to_categories['kenya-school-of-law'] = set([u'education'])
    oslug_to_categories['alliance-high-school'] = set([u'education'])
    oslug_to_categories['jomo-kenyatta-university-of-agriculture-technology-jkuat'] = set([u'education'])
    oslug_to_categories['moi-high-school-kabarak'] = set([u'education'])
    oslug_to_categories['nairobi-school'] = set([u'education'])
    oslug_to_categories['parliament'] = set([u'political'])
    oslug_to_categories['national-assembly'] = set([u'political'])

    errors = []

    for slug, categories in oslug_to_categories.items():
        if len(categories) > 1 and 'other' in categories:
            categories.discard('other')
        if len(categories) == 1:
            oslug_to_category[slug] = list(categories)[0]
        else:
            message = "There were %d for organisation %s: %s" % (len(categories), slug, categories)
            errors.append(message)
        all_categories = all_categories | categories

    if errors:
        for error in errors:
            print >> sys.stderr, error
        raise Exception, "Found organisations with multiple categories other than 'other'"

    for o in Organisation.objects.all():
        properties = {'slug': o.slug,
                      'name': o.name.strip(),
                      'classification': o.kind.name}
        if o.slug in oslug_to_category:
            properties['category'] = oslug_to_category[o.slug]
        add_start_and_end_date(
            o,
            properties,
            start_key_map=('started', 'founding_date'),
            end_key_map=('ended', 'dissolution_date'))
        add_identifiers_to_properties(o, properties, primary_id_scheme)
        add_contact_details_to_properties(o, properties)
        result.append(properties)
        country.add_extra_popolo_data_for_organization(o, properties, base_url)
    return result

def create_organisations(popit, primary_id_scheme, base_url):
    """Create organizations in PopIt based on those used in memberships in Pombola

    Look through all memberships in PopIt and find add the organization
    that each refers to to PopIt.  Returns a dictionary where each key
    is a slug for an organisation in Pombola, and the value is the
    corresponding ID for the organization in PopIt.
    """

    for organization in get_organizations(primary_id_scheme, base_url):
        print >> sys.stderr, "creating the organisation:", organization['name']
        try:
            popit.organizations.post(organization)
        except slumber.exceptions.HttpServerError:
            print >> sys.stderr, "Failed POSTing the organisation:"
            print >> sys.stderr, json.dumps(organization, indent=4)
            raise

def get_people(primary_id_scheme, base_url, inline_memberships=True):

    result = {
        'persons': []
    }
    if not inline_memberships:
        result['memberships'] = []

    for person in Person.objects.all():
        name = person.legal_name
        person_properties = {'name': name}
        for date, key in ((person.date_of_birth, 'birth_date'),
                          (person.date_of_death, 'death_date')):
            if date:
                person_properties[key] = date_to_partial_iso8601(date)
        primary_image = person.primary_image()
        if primary_image:
            person_properties['images' ] = [
                {
                    'url': urljoin(base_url, primary_image.url)
                }
            ]
        add_identifiers_to_properties(person, person_properties, primary_id_scheme)
        add_contact_details_to_properties(person, person_properties)
        add_other_names(person, person_properties)
        for key in extra_popolo_person_fields:
            value = getattr(person, key)
            # This might be a markitup.fields.Markup field, in
            # which case we need to call raw on it:
            try:
                value = value.raw
            except AttributeError:
                pass
            if value:
                person_properties[key] = value
        country.add_extra_popolo_data_for_person(person, person_properties, base_url)

        if inline_memberships:
            person_properties['memberships'] = []

        for position in person.position_set.all():
            properties = {'person_id': person.get_popolo_id(primary_id_scheme)}
            if position.title and position.title.name:
                properties['role'] = position.title.name
            add_start_and_end_date(position, properties)
            add_identifiers_to_properties(position, properties, primary_id_scheme)
            if position.organisation:
                position.organisation.slug
                organization_id = position.organisation.get_popolo_id(primary_id_scheme)
                properties['organization_id'] = organization_id
            if inline_memberships:
                person_properties['memberships'].append(properties)
            else:
                result['memberships'].append(properties)

        result['persons'].append(person_properties)
    return result

def get_popolo_data(primary_id_scheme, base_url, inline_memberships=True):
    result = get_people(primary_id_scheme, base_url, inline_memberships)
    result['organizations'] = get_organizations(primary_id_scheme, base_url)
    return result

def create_people(popit, primary_id_scheme, base_url):
    data = get_people(primary_id_scheme, base_url, inline_memberships=False)
    try:
        for singular in ('person', 'membership'):
            collection = singular + 's'
            popit_collection = getattr(popit, collection)
            for properties in data[collection]:
                if singular == 'person':
                    message = "creating the person: " + properties['name']
                else:
                    fmt = "creating the membership {0} => {1}"
                    message = fmt.format(properties['person_id'],
                                         properties['organization_id'])
                print >> sys.stderr, message
                popit_collection.post(properties)
    except slumber.exceptions.HttpServerError:
        print >> sys.stderr, "Failed POSTing the {0}:".format(singular)
        print >> sys.stderr, json.dumps(person, indent=4)
        raise
