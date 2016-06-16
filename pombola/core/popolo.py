import sys
import slumber
import json
import datetime
from collections import defaultdict
from urlparse import urljoin

from django.core.urlresolvers import reverse

from mapit.views.areas import area

from pombola.core.models import (
    Organisation, ParliamentarySession, Person, Place, Position
)
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

def get_area_information(place, base_url):
    """Given a PopIt place, generate a Popolo area dictionary

    The Popolo specification doesn't have much detail about how the
    area attribute of a position or post should be constructed so this
    just follows the convention in YourNextRepresentative's data but
    with additional fields for the parliamentary session (if available)
    and the MapIt area type."""
    mapit_area = place.mapit_area
    if mapit_area is None:
        return None
    mapit_id = mapit_area.id
    mapit_type = mapit_area.type.code
    path = reverse(area, kwargs={'area_id': mapit_id})
    result = {
        'id': 'mapit:{0}'.format(place.mapit_area.id),
        'identifier': urljoin(base_url, path),
        'area_type': mapit_type,
        'name': place.name,
    }
    session = place.parliamentary_session
    if session:
        result['session'] = {
            'id': session.id,
            'name': session.name,
            'start_date': str(session.start_date),
            'end_date': str(session.end_date),
            'mapit_generation': session.mapit_generation,
            'house_id': session.house.id,
            'house_name': session.house.name,
        }
    return result

def date_to_partial_iso8601(approx_date):
    """Get a (possibly partial) ISO 8601 representation of an ApproximateDate
    >>> from django_date_extensions.fields import ApproximateDate

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

def get_events(primary_id_scheme, base_url):
    result = []
    for ps in ParliamentarySession.objects.all():
        result.append({
            'classification': 'legislative period',
            'start_date': str(ps.start_date),
            'end_date': str(ps.end_date),
            'id': ps.slug,
            'organization_id': ps.house.get_popolo_id(primary_id_scheme),
            'name': ps.name,
        })
    return result

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

def get_areas(primary_id_scheme, base_url):
    all_areas = [
        get_area_information(pl, base_url) for pl in Place.objects.all()
    ]
    return [a for a in all_areas if a is not None]

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

def get_people(primary_id_scheme, base_url, title_to_sessions, inline_memberships=True):

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
            if position.place:
                # If there's a place associated with the position, set that on
                # the position as an area:
                properties['area'] = get_area_information(position.place, base_url)
            possible_events = []
            if position.title:
                possible_events = title_to_sessions.get(position.title.slug, [])
            if possible_events:
                # Order them by overlap:
                events_with_overlap = [
                    (position.approximate_date_overlap(e.start_date, e.end_date), e)
                    for e in possible_events
                ]
                events_with_overlap.sort(reverse=True, key=lambda t: t[0])
                # n.b. There's an assumption here that if someone's an
                # MP in consecutive terms, that's represented by two
                # positions rather than one. (In most cases that
                # better models reality anyway.0
                most_likely_event = events_with_overlap[0]
                properties['legislative_period_id'] = most_likely_event[1].slug
            if inline_memberships:
                person_properties['memberships'].append(properties)
            else:
                result['memberships'].append(properties)

        result['persons'].append(person_properties)
    return result

def get_popolo_data(primary_id_scheme, base_url, inline_memberships=True):
    title_to_sessions = {}
    for ps in ParliamentarySession.objects.select_related(
            'house', 'position_title'):
        if ps.position_title:
            title_slug = ps.position_title.slug
        else:
            title_slug = None
        title_to_sessions.setdefault(title_slug, [])
        title_to_sessions[title_slug].append(ps)
    for sessions in title_to_sessions.values():
        sessions.sort(key=lambda s: s.start_date)
    result = get_people(
        primary_id_scheme,
        base_url,
        title_to_sessions,
        inline_memberships,
    )
    result['organizations'] = get_organizations(primary_id_scheme, base_url)
    result['events'] = get_events(primary_id_scheme, base_url)
    result['areas'] = get_areas(primary_id_scheme, base_url)
    result['posts'] = []
    return result

def create_people(popit, primary_id_scheme, base_url):
    data = get_people(primary_id_scheme, base_url, inline_memberships=False)
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
            try:
                popit_collection.post(properties)
            except slumber.exceptions.HttpServerError:
                print >> sys.stderr, "Failed POSTing the {0}:".format(singular)
                print >> sys.stderr, json.dumps(properties, indent=4)
                raise
