import json
import re
import time
import unicodedata
import urllib
from optparse import make_option

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management.base import LabelCommand
from django.utils.text import slugify

from pombola.core.models import (
    Contact,
    ContactKind,
    Identifier,
    Organisation,
    OrganisationKind,
    Person,
    Place,
    PlaceKind,
    Position,
    PositionTitle,
    )
from pombola.images.models import Image
from mapit.models import Area, Generation


VERBOSE = False

# Use these to spot any fields that exist in the input data, but we
# aren't either already dealing with, or deliberately ignoring:

known_fields = {
    'person': {'used': set(('id',
                            'honorific_prefix',
                            'name',
                            'slug',
                            'image',
                            'identifiers',
                            'contact_details',
                            'other_names',
                            'biography',
                            'memberships',)),
               'ignored': set(('family_name',
                               'initials_alt',
                               'given_names',))},
    'membership': {'used': set(('id',
                                'organization_id',
                                'person_id',
                                'role',
                                'area',
                                'start_date',
                                'end_date')),
                   'ignored': set(('label',
                                   # FIXME: Pombola needs start/end_reason
                                   'end_reason'))},
    'contact_detail': {'used': set(('type',
                                    'note',
                                    'value')),
                       'ignored': set()}}

def check_unknown_field(entity, key):
    d = known_fields[entity]
    if not ((key in d['used']) or (key in d['ignored'])):
        print "WARNING: unknown %s field: %s" % (entity, key)

def get_position_title(role, organisation_name, organisation_kind_name):
    if organisation_kind_name == 'Party' or 'Committee' in organisation_kind_name:
        if role:
            return role
        return 'Member'

    if not role:
        raise Exception, "No role specified, and unknown organisation kind: " + organisation_kind_name

    return role

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
            o.save()
            verbose(" (saved)")
        else:
            verbose(" (not saving)")
        return o
    raise Exception("Failed get_or_create")


def add_image_to_object(image_url, obj, commit):
    source = "Downloaded from: %s" % (image_url,)
    if Image.objects.filter(source=source).count() > 0:
        if VERBOSE:
            print "  (image already imported)"
    else:
        person_image = get_or_create(Image,
                                     commit=commit,
                                     source=source,
                                     defaults={'content_object': obj})
        if commit:
            print "  (downloading %s)" % (image_url,)
            response = urllib.urlopen(image_url)
            status_code = response.getcode()
            if status_code < 200 or status_code >= 300:
                message = "Unexpected HTTP status %d on downloading '%s'"
                raise RuntimeError, message % (status_code, image_url)
            content = ContentFile(response.read())
            time.sleep(2)
            # The image name is used to generate its
            # filename, and if it contains non-ASCII
            # characters that can cause unpredictable
            # locale-dependent problems, so remove any
            # accents:
            normalized_name = unicodedata.normalize("NFKD", obj.name).encode("ascii", "ignore")
            person_image.image.save(
                name = 'Picture of ' + normalized_name,
                content=content)


class Command(LabelCommand):
    help = 'Import people, organisations and positions from Popolo JSON'
    args = '<Popolo JSON files>'

    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--delete-old', action='store_true', dest='delete_old', help='Delete old positions, contacts, and alternative names and identifiers, assuming we have complete information to recreate them'),
        )

    def handle_label(self,  input_filename, **options):

        # FIXME: currently this script relies on the slugs and names
        # of organisations and people being unique, since we don't
        # have stable IDs for the South African data.  For other
        # purposes this assumption will likely not be true, and the
        # script will need to be changed.
        #
        # Note that this may be further complicated because we use 'slugify' to
        # ensure that the slugs created in the database are correct, which might
        # mean that they differ from the data boing imported. Also this
        # slugification may lead to slug that were unique in the raw data being
        # the same in the database.

        global VERBOSE
        VERBOSE = int(options['verbosity']) > 1

        with open(input_filename) as fp:
            popolo_data = json.load(fp)

        id_to_organisation = {}

        # First import all the organizations as Organisation objects
        # in Pombola:

        for organisation in popolo_data['organizations']:
            o_id = organisation['id']

            if 'classification' not in organisation:
                raise Exception, "No classfication found in '%s'" % (o_id,)

            classification = organisation['classification']

            o_kind = get_or_create(OrganisationKind,
                                   commit=options['commit'],
                                   slug=slugify(classification),
                                   defaults={'name': classification.title()})

            o = get_or_create(Organisation,
                              commit=options['commit'],
                              slug=slugify(organisation['slug']),
                              kind=o_kind,
                              defaults={'name': organisation['name']})
            if options['commit']:
                o.save()

            if 'image' in organisation:
                add_image_to_object(image_url=organisation['image'], obj=o, commit=options['commit'])


            id_to_organisation[o_id] = o

            create_identifiers(organisation, o, options['commit'])

        person_content_type = ContentType.objects.get_for_model(Person)

        current_mapit_generation = Generation.objects.current()

        # Import all the people as Person objects in Pombola:

        for person in popolo_data['persons']:

            for k in person.keys():
                check_unknown_field('person', k)

            title = person.get('honorific_prefix')

            name = person['name']

            defaults = {'legal_name': name}
            if title:
                defaults['title'] = title

            slug = slugify(person['slug'])

            p = get_or_create(Person,
                              commit=options['commit'],
                              slug=slug,
                              defaults=defaults)

            if options['commit'] and options['delete_old']:
                Identifier.objects.filter(
                    content_type=ContentType.objects.get_for_model(Person),
                    object_id=p.id,
                ).delete()

            create_identifiers(person, p, options['commit'])

            if options['commit'] and options['delete_old']:
                p.alternative_names.all().delete()

            if 'other_names' in person:
                # FIXME: check the exact intended meaning of this
                # field - in sa.json many appear to just be surnames,
                # but some are full names.
                for other_name in person['other_names']:
                    p.add_alternative_name(other_name['name'])

            if 'image' in person:
                add_image_to_object(image_url=person['image'], obj=p, commit=options['commit'])

            # Create a Contact object for each contact in the JSON:

            # We may have been asked to remove all previous contact details for this person:
            if options['commit'] and options['delete_old']:
                p.contacts.all().delete()

            for contact in person.get('contact_details', []):

                for k in contact.keys():
                    check_unknown_field('contact_detail', k)

                contact_type = contact['type']
                c_kind = get_or_create(ContactKind,
                                       commit=options['commit'],
                                       slug=slugify(contact_type),
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

                for k in membership.keys():
                    check_unknown_field('membership', k)

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
                if place:
                    kwargs['place'] = place

                m = get_or_create(Position, **kwargs)

                create_identifiers(membership, m, options['commit'])
