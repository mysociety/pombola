import os
import sys
import re
from optparse import make_option

import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand

from django.utils.text import slugify

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import ( ContentType, ContactKind, Identifier,
    Organisation, Person, Contact )

def parse_approximate_date(s):
    """Take a partial ISO 8601 date, and return an ApproximateDate for it

    >>> ad = parse_approximate_date('2014-02-17')
    >>> type(ad)
    <class 'django_date_extensions.fields.ApproximateDate'>
    >>> ad
    2014-02-17
    >>> parse_approximate_date('2014-02')
    2014-02-00
    >>> parse_approximate_date('2014')
    2014-00-00
    """

    for regexp in [
        r'^(\d{4})-(\d{2})-(\d{2})$',
        r'^(\d{4})-(\d{2})$',
        r'^(\d{4})$'
    ]:
        m = re.search(regexp, s)
        if m:
            return ApproximateDate(*(int(g, 10) for g in m.groups()))
    if s == 'future':
        return ApproximateDate(future=True)
    raise Exception, "Couldn't parse '{0}' as an ApproximateDate".format(s)

class Command(LabelCommand):

    help = 'Imports the South Africa Popolo JSON into Pombola.'

    def handle_label(self, filename, **options):

        with open(filename) as f:
            data = json.load(f)

        # Get the common identifier types to save hammering the DB

        content_type_org = ContentType.objects.get_for_model(Organisation)
        content_type_person = ContentType.objects.get_for_model(Person)

        contact_kind_email = ContactKind.objects.get(slug='email')
        contact_kind_voice = ContactKind.objects.get(slug='voice')
        contact_kind_cell = ContactKind.objects.get(slug='cell')
        contact_kind_phone = ContactKind.objects.get(slug='phone')
        contact_kind_fax = ContactKind.objects.get(slug='fax')
        contact_kind_address = ContactKind.objects.get(slug='address')

        # Handle the organisations...

        for json_org in data['organizations']:

            # Make sure the organisation can be matched, otherwise this is pointless
            try:
                pombola_org = Organisation.objects.get(slug=json_org['slug'])
            except Organisation.DoesNotExist:
                print >> sys.stderr, 'Could not match ' + json_org['name'] + ' on slug "' + json_org['slug'] + '".'
                sys.exit(1)
            except Organisation.MultipleObjectsReturned:
                print >> sys.stderr, 'Multiple objects returned for slug "' + json_org['slug'] + '".'
                sys.exit(1)

            if 'founding_date' in json_org:
                pombola_org.started = parse_approximate_date(json_org['founding_date'])

            if 'dissolution_date' in json_org:
                pombola_org.ended = parse_approximate_date(json_org['dissolution_date'])

            pombola_org.save()

            # # Slice up the identifier
            identifier_scheme, _, identifier_identifier = json_org['id'].rpartition('/')

            # Pop the identifier back in the database. Use get_or_create so this is idempotent.
            Identifier.objects.get_or_create(
                scheme = identifier_scheme,
                identifier = identifier_identifier,
                object_id = pombola_org.id,
                content_type = content_type_org,
            )

            # If the Organisation has any more identifiers, iterate over those and insert as well.

            if 'identifiers' in json_org:
                for org_identifier in json_org['identifiers']:
                    Identifier.objects.get_or_create(
                        scheme = org_identifier['scheme'],
                        identifier = org_identifier['identifier'],
                        object_id = pombola_org.id,
                        content_type = content_type_org,
                    )

        # Handle the people

        for json_person in data['persons']:

            # Make sure the organisation can be matched, otherwise this is pointless
            try:
                pombola_person = Person.objects.get(slug=json_person['slug'])
            except Person.DoesNotExist:
                print >> sys.stderr, 'Could not match ' + json_person['name'] + ' on slug "' + json_person['slug'] + '".'
                sys.exit(1)
            except Person.MultipleObjectsReturned:
                print >> sys.stderr, 'Multiple objects returned for slug "' + json_person['slug'] + '".'
                sys.exit(1)

            # Update the details. We may or may not have these things.

            if 'email' in json_person:
                pombola_person.email = json_person['email']

            if 'family_name' in json_person:
                pombola_person.family_name = json_person['family_name']

            if 'given_names' in json_person:
                pombola_person.given_name = json_person['given_names']

            if 'additional_name' in json_person:
                pombola_person.additional_name = json_person['additional_name']

            if 'sort_name' in json_person:
                pombola_person.sort_name = json_person['sort_name']

            if 'honorific_prefix' in json_person:
                pombola_person.honorific_prefix = json_person['honorific_prefix']

            if 'honorific_suffix' in json_person:
                pombola_person.honorific_suffix = json_person['honorific_suffix']

            if 'summary' in json_person:
                pombola_person.biography = json_person['summary']

            if 'biography' in json_person:
                pombola_person.biography = json_person['biography']

            if 'national_identity' in json_person:
                pombola_person.national_identity = json_person['national_identity']

            if 'gender' in json_person:
                pombola_person.gender = json_person['gender']

            # Save the changes to the person!
            pombola_person.save()

            # Look to see if there are any new contact details we can insert
            if 'contact_details' in json_person:
                for contact_detail in json_person['contact_details']:

                    # These are done separately in case we ever need to do manipulation

                    if contact_detail['type'] == 'email':
                        Contact.objects.get_or_create(
                            kind = contact_kind_email,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )
                        # We *could* do this, but no way of determining primary.
                        # pombola_person.email = contact_detail['value']

                    elif contact_detail['type'] == 'voice':
                        Contact.objects.get_or_create(
                            kind = contact_kind_voice,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )

                    elif contact_detail['type'] == 'cell':
                        Contact.objects.get_or_create(
                            kind = contact_kind_cell,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )

                    elif contact_detail['type'] == 'phone':
                        Contact.objects.get_or_create(
                            kind = contact_kind_phone,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )

                    elif contact_detail['type'] == 'fax':
                        Contact.objects.get_or_create(
                            kind = contact_kind_fax,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )

                    elif contact_detail['type'] == 'address':
                        Contact.objects.get_or_create(
                            kind = contact_kind_address,
                            value = contact_detail['value'],
                            object_id = pombola_person.id,
                            content_type = content_type_person,
                        )

                    else:
                        print >> sys.stderr, 'Unmatched contact type "' + contact_detail['type'] + '".'

            # Slice up the identifier
            identifier_scheme, _, identifier_identifier = json_person['id'].rpartition('/')

            # Pop the identifier back in the database. Use get_or_create so this is idempotent.
            Identifier.objects.get_or_create(
                scheme = identifier_scheme,
                identifier = identifier_identifier,
                object_id = pombola_person.id,
                content_type = content_type_person,
            )

            # If the Person has any more identifiers, iterate over those and insert as well.

            if 'identifiers' in json_person:
                for person_identifier in json_person['identifiers']:
                    Identifier.objects.get_or_create(
                        scheme = person_identifier['scheme'],
                        identifier = person_identifier['identifier'],
                        object_id = pombola_person.id,
                        content_type = content_type_person,
                    )
