import sys
import re

import json

from django.core.management.base import LabelCommand

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Organisation, Person


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
