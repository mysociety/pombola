# This command creates a new PopIt instance based on the Person,
# Position and Organisation models in Pombola.

import re
import sys
import os
import slumber
import json
import datetime
import urlparse
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person, Organisation, Position

# n.b. We no longer have the old PopIt API in requirements.txt, so
# comment this out; the script is largely here for reference at the
# moment, to be replaced by a Popolo JSON export.

from popit_api import PopIt

from optparse import make_option

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

def add_identifiers_to_properties(o, properties):
    primary_id_scheme = 'org.mysociety.za'
    secondary_identifiers = []
    for scheme, identifiers in o.get_all_identifiers().items():
        sorted_identifiers = sorted(identifiers)
        if scheme == primary_id_scheme:
            properties['id'] = scheme + sorted_identifiers[0]
        else:
            secondary_identifiers.append({
                'scheme': scheme,
                'identifier': sorted_identifiers[0]
            })
    properties['identifiers'] = secondary_identifiers

def create_organisations(popit):
    """Create organizations in PopIt based on those used in memberships in Pombola

    Look through all memberships in PopIt and find add the organization
    that each refers to to PopIt.  Returns a dictionary where each key
    is a slug for an organisation in Pombola, and the value is the
    corresponding ID for the organization in PopIt.
    """

    oslug_to_categories = defaultdict(set)

    for pos in Position.objects.all():
        if pos.organisation:
            slug = pos.organisation.slug
            oslug_to_categories[slug].add(pos.category)

    all_categories = set()
    oslug_to_category = {}

    oslug_to_categories['university-of-nairobi'] = set([u'education'])
    oslug_to_categories['parliament'] = set([u'political'])

    for slug, categories in oslug_to_categories.items():
        if len(categories) > 1 and 'other' in categories:
            categories.discard('other')
        if len(categories) == 1:
            oslug_to_category[slug] = list(categories)[0]
        else:
            message = "There were %d for organisation %s: %s" % (len(categories), slug, categories)
            # print >> sys.stderr, message
            raise Exception, message
        all_categories = all_categories | categories

    slug_to_id = {}

    for o in Organisation.objects.all():
        if o.slug in oslug_to_category:
            print >> sys.stderr, "creating the organisation:", o.name
            properties = {'slug': o.slug,
                          'name': o.name,
                          'classification': o.kind.name,
                          'category': oslug_to_category[o.slug]}
            add_identifiers_to_properties(o, properties)
            new_organisation = popit.organizations.post(properties)
            slug_to_id[o.slug] = new_organisation['result']['id']
    return slug_to_id

class Command(BaseCommand):
    args = 'MZALENDO-URL'
    help = 'Take all people in Pombola and import them into a PopIt instance'
    option_list = BaseCommand.option_list + (
            make_option("--instance", dest="instance",
                        help="The name of the PopIt instance (e.g. ukcabinet)",
                        metavar="INSTANCE"),
            make_option("--hostname", dest="hostname",
                        default="popit.mysociety.org",
                        help="The PopIt hostname (default: popit.mysociety.org)",
                        metavar="HOSTNAME"),
            make_option("--user", dest="user",
                        help="Your username", metavar="USERNAME"),
            make_option("--password", dest="password",
                        help="Your password", metavar="PASSWORD"),
            make_option("--port", dest="port",
                        help="port (default: 80)", metavar="PORT"),
            make_option("--test", dest="test", action="store_true",
                        help="run doctests", metavar="PORT"),
            )

    def handle(self, *args, **options):

        if options['test']:
            import doctest
            failure_count, _ = doctest.testmod(sys.modules[__name__])
            sys.exit(0 if failure_count == 0 else 1)

        popit_option_keys = ('instance', 'hostname', 'user', 'password', 'port')
        popit_options = dict((k, options[k]) for k in popit_option_keys if options[k] is not None)
        popit_options['api_version'] = 'v0.1'

        if len(args) != 1:
            raise CommandError, "You must provide the base URL of the public Pombola site"

        try:
            popit = PopIt(**popit_options)

            base_url = args[0]
            parsed_url = urlparse.urlparse(base_url)

            message = "WARNING: this script will delete everything in the PopIt instance %s on %s.\n"
            message += "If you want to continue with this, type 'Yes': "

            response = raw_input(message % (popit.instance, popit.hostname))
            if response != 'Yes':
                print >> sys.stderr, "Aborting."
                sys.exit(1)

            if parsed_url.path or parsed_url.params or parsed_url.query or parsed_url.fragment:
                raise CommandError, "You must only provide the base URL"

            # Remove all the "person", "organization" and "membership"
            # objects from PopIt.  Currently there's no command to
            # delete all in one go, so we have to do it one-by-one.

            for schema_singular in ('person', 'organization', 'membership'):
                while True:
                    plural = schema_singular + 's'
                    response = getattr(popit, plural).get()
                    for o in response['result']:
                        print >> sys.stderr, "deleting the {0}: {1}".format(
                            schema_singular, o)
                        getattr(popit, plural)(o['id']).delete()
                    if not response.get('has_more', False):
                        break

            # Create all the organisations found in Pombola, and get
            # back a dictionary mapping the Pombola organisation slug
            # to the PopIt ID.

            org_slug_to_id = create_organisations(popit)

            # Create a person in PopIt for each Person in Pombola:

            for person in Person.objects.all():
                name = person.legal_name
                print >> sys.stderr, "creating the person:", name
                person_properties = {'name': name}
                for date, key in ((person.date_of_birth, 'birth_date'),
                                  (person.date_of_death, 'death_date')):
                    if date:
                        person_properties[key] = date_to_partial_iso8601(date)
                primary_image = person.primary_image()
                if primary_image:
                    person_properties['images' ] = [{'url': base_url + primary_image.url}]
                add_identifiers_to_properties(person, person_properties)
                person_id = popit.persons.post(person_properties)['result']['id']
                for position in person.position_set.all():
                    if not (position.title and position.title.name):
                        continue
                    properties = {'role': position.title.name,
                                  'person_id': person_id}
                    if position.start_date and not position.start_date.past:
                        properties['start_date'] = date_to_partial_iso8601(position.start_date)
                    if position.end_date and not position.end_date.future:
                        properties['end_date'] = date_to_partial_iso8601(position.end_date)
                    add_identifiers_to_properties(position, properties)
                    if position.organisation:
                        oslug = position.organisation.slug
                        organization_id = org_slug_to_id[oslug]
                        properties['organization_id'] = organization_id
                    print >> sys.stderr, "  creating the membership:", position
                    new_membership = popit.memberships.post(properties)

        except slumber.exceptions.HttpClientError, e:
            print "Exception is:", e
            print "Error response content is", e.content
            sys.exit(1)
