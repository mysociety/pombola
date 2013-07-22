import json
import re
import sys
import time
import urllib
from urlparse import urlsplit, urlunsplit
from optparse import make_option

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management.base import LabelCommand, CommandError
from django.template.defaultfilters import slugify

from core.models import (Organisation, OrganisationKind, Identifier,
                         PlaceKind, Person, Contact, ContactKind, Position,
                         PositionTitle, Place, PlaceKind)
from images.models import Image
from mapit.models import Area, Generation

VERBOSE = False

def get_position_title(role, organisation_name, organisation_kind_name):

    # FIXME: this temporary code is specific to South Africa, and
    # should be removed if we have JSON where the membership roles are
    # slightly more specific.  Alternatively, we could add an extra
    # view to Mzalendo to show positions with a pariticular
    # Organisation and OrganisationKind.

    if not role:
        okind = organisation_kind_name
        if okind in ('Party', 'Committee'):
            return okind + ' Member'
        else:
            raise Exception, "No role specified, and unknown organisation kind:" + okind

    if organisation_kind_name == "House":
        if role == "Member" and organisation_name == "National Assembly":
            return "NA Member"
        elif role == "Delegate" and organisation_name == "National Council of Provinces":
            return "NCOP Delegate"

    return role

def fix_url(url):
    # The path component of the URLs in the current South African
    # Popolo JSON have Unicode characters that need to be UTF-8
    # encoded and percent-escaped:
    parts = urlsplit(url)
    fixed_path = urllib.quote(parts.path.encode('UTF-8'))
    parts = list(parts)
    parts[2] = fixed_path
    return urlunsplit(parts)

def verbose(message):
    """Output message only if VERBOSE is set"""
    if VERBOSE:
        print message.encode('utf-8')

known_id_schemes = ('org.mysociety.za',
                    'myreps_id',
                    'myreps_person_id',
                    'za.gov.parliament')

id_re = re.compile('^(?P<scheme>' + '|'.join(known_id_schemes) + ')' +
                   '(?P<identifier>.*)$')

def split_popolo_id(popolo_id):
    """Take a popolo ID and split it into the scheme and the identifier"""
    m = id_re.search(popolo_id)
    if not m:
        message = "The ID '%s' didn't match %s" % (popolo_id, id_re.pattern)
        raise Exception, message
    return m.groups()

def create_identifiers(popolo_entity, mz_object, commit=True):
    """Create all Identifier objects for mz_object based on popolo_entity"""
    popolo_id_scheme, popolo_id_identifier = split_popolo_id(popolo_entity['id'])

    mz_object_content_type = ContentType.objects.get_for_model(mz_object)

    get_or_create(Identifier,
                  commit=commit,
                  scheme=popolo_id_scheme,
                  identifier=popolo_id_identifier,
                  defaults={'object_id': mz_object.id,
                            'content_type': mz_object_content_type})

    if 'identifiers' in popolo_entity:
        for identifier in popolo_entity['identifiers']:
            get_or_create(Identifier,
                          commit=commit,
                          scheme=identifier['scheme'],
                          identifier=identifier['identifier'],
                          defaults={'object_id': mz_object.id,
                                   'content_type': mz_object_content_type})

def get_or_create(model, **kwargs):
    """An alternative to Django's get_or_create where save() is optional

    This is based on Django's get_or_create from
    django/db/models/query.py, but in this version the special keyword
    argument 'commit' (which defaults to True) can be set to False to
    specify that the model shouldn't be saved."""

    commit = kwargs.pop('commit', True)
    defaults = kwargs.pop('defaults', {})
    lookup = kwargs.copy()
    try:
        return model.objects.get(**lookup)
    except model.DoesNotExist:
        params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
        params.update(defaults)
        if VERBOSE:
            print "Creating %s with parameters:" % (model.__name__,)
            for k, v in params.items():
                print "  " + k + ": " + unicode(v).encode('utf-8')
        o = model(**params)
        if commit:
            verbose(" (saved)")
            o.save()
        else:
            verbose(" (not saving)")
    return o

class Command(LabelCommand):
    help = 'Import people, organisations and positions from Popolo JSON'
    args = '<Popolo JSON files>'

    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--delete-old', action='store_true', dest='delete_old', help='Delete old positions and contacts, assuming we have complete information to recreate them'),
        )

    def handle_label(self,  input_filename, **options):

        # FIXME: currently this script relies on the slugs and names
        # of organisations and people being unique, since we don't
        # have stable IDs for the South African data.  For other
        # purposes this assumption will likely not be true, and the
        # script will need to be changed.

        global VERBOSE
        VERBOSE = int(options['verbosity']) > 1

        with open(input_filename) as fp:
            popolo_data = json.load(fp)

        id_to_organisation = {}

        # First import all the organizations as Organisation objects
        # in Mzalendo:

        for organisation in popolo_data['organizations']:
            o_id = organisation['id']

            if 'classification' not in organisation:
                raise Exception, "No classfication found in '%s'" % (o_id,)

            classification = organisation['classification']

            o_kind = get_or_create(OrganisationKind,
                                   commit=options['commit'],
                                   slug=classification,
                                   defaults={'name': classification.title()})

            o = get_or_create(Organisation,
                              commit=options['commit'],
                              slug=organisation['slug'],
                              kind=o_kind,
                              defaults={'name': organisation['name']})
            if options['commit']:
                o.save()

            id_to_organisation[o_id] = o

            create_identifiers(organisation, o, options['commit'])

        person_content_type = ContentType.objects.get_for_model(Person)

        current_mapit_generation = Generation.objects.current()

        # Import all the people as Person objects in Mzalendo:

        for person in popolo_data['persons']:

            title = person.get('honorific_prefix')

            name = person['name']

            defaults = {'legal_name': name}
            if title:
                defaults['title'] = title

            slug = person['slug']

            p = get_or_create(Person,
                              commit=options['commit'],
                              slug=slug,
                              defaults=defaults)

            create_identifiers(person, p, options['commit'])

            if 'image' in person:
                image_url = fix_url(person['image'])
                source = "Downloaded from: %s" % (image_url,)
                if Image.objects.filter(source=source).count() > 0:
                    if VERBOSE:
                        print "  (image already imported)"
                else:
                    person_image = get_or_create(Image,
                                                 commit=options['commit'],
                                                 source=source,
                                                 defaults={'content_object': p})
                    if options['commit']:
                        print "  (downloading %s)" % (image_url,)
                        content = ContentFile(urllib.urlopen(image_url).read())
                        time.sleep(2)
                        person_image.image.save(
                            name = 'Picture of ' + p.name,
                            content=content)

            # Create a Contact object for each contact in the JSON:

            # We may have been asked to remove all previous contact details for this person:
            if options['commit'] and options['delete_old']:
                p.contacts.all().delete()

            for contact in person.get('contact_details', []):
                contact_type = contact['type']
                c_kind = get_or_create(ContactKind,
                                       commit=options['commit'],
                                       slug=contact_type,
                                       defaults={'name': contact_type.title()})
                defaults = {'value': contact['value']}
                if 'note' in contact:
                    defaults['note'] = contact['note']
                c = get_or_create(Contact,
                                  commit=options['commit'],
                                  kind=c_kind,
                                  object_id=p.id,
                                  content_type=person_content_type,
                                  defaults=defaults)

            # Create a Position object for each membership in the JSON:

            # We may have been asked to remove all previous memberships for this person:
            if options['commit'] and options['delete_old']:
                p.position_set.all().delete()

            for membership in person['memberships']:

                organisation = id_to_organisation[membership['organization_id']]

                position_title_name = get_position_title(membership.get('role'),
                                                         organisation.name,
                                                         organisation.kind.name)

                # FIXME: also decide about PositionTitle.requires_place
                position_title = get_or_create(PositionTitle,
                                               commit=options['commit'],
                                               name=position_title_name,
                                               defaults={'slug': slugify(position_title_name)})

                place = None
                if "area" in membership:
                    area = membership['area']
                    area_name = area['name']
                    area_scheme, area_id = split_popolo_id(area['id'])
                    m = re.search('^/mapit/code/(\w+)/(\w+)$', area_id)
                    if not m:
                        raise Exception, "Unknown area ID: " + area_id
                    code_type, code_code = m.groups()

                    area = Area.objects.get(codes__type__code=code_type,
                                            codes__code=code_code,
                                            generation_low__lte=current_mapit_generation,
                                            generation_high__gte=current_mapit_generation)

                    # FIXME: it would be nice to get the singular and
                    # plural versions of PlaceKind names correct, but
                    # that's not easy to do automatically:

                    placekind_name = area.type.description

                    placekind = get_or_create(PlaceKind,
                                              commit=options['commit'],
                                              name=placekind_name,
                                              slug=slugify(placekind_name),
                                              defaults={'plural_name': placekind_name})

                    place = get_or_create(Place,
                                          commit=options['commit'],
                                          name = area.name,
                                          kind=placekind,
                                          defaults={'slug': slugify(area.name),
                                                    'mapit_area': area})

                kwargs = {'commit': options['commit'],
                          'person': p,
                          'organisation': organisation,
                          'title': position_title,
                          'category': 'political'}
                for field in ('start_date', 'end_date'):
                    if field in membership:
                        kwargs[field] = membership[field]

                m = get_or_create(Position, **kwargs)

                create_identifiers(membership, m, options['commit'])
