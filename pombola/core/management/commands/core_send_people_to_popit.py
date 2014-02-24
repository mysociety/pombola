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

# from popit import PopIt

from optparse import make_option

def date_to_iso_datetime(passed_date):
    """Convert a date to a datetime and return an ISO-8601 representation

    >>> date_to_iso_datetime(datetime.date(2011, 4, 5))
    '2011-04-05T00:00:00'
    """

    return datetime.datetime.combine(passed_date, datetime.time()).isoformat()

def date_to_popit_partial_date(approx_date):
    """Return a PopIt partial date from a Django approximate date

    A full date returns 00:00 at the beginning of that day as both the
    start and end date:

    >>> date_to_popit_partial_date(ApproximateDate(2012, 6, 2))
    {'start': '2012-06-02T00:00:00', 'end': '2012-06-02T00:00:00', 'formatted': '02 June 2012'}

    Just a year returns 00:00 on the 1st of January as the start, and
    00:00 on the 31st of December as the end date:

    >>> date_to_popit_partial_date(ApproximateDate(2010))
    {'start': '2010-01-01T00:00:00', 'end': '2010-12-31T00:00:00', 'formatted': '2010'}

    Just a year and a month returns 00:00 on the first day of the
    month as the start, and 00:00 on the final day of the month as the
    end date:

    >>> date_to_popit_partial_date(ApproximateDate(2012, 2))
    {'start': '2012-02-01T00:00:00', 'end': '2012-02-29T00:00:00', 'formatted': '2/2012'}

    If the approx_date is 'future' or falsy, just return the null date:

    >>> date_to_popit_partial_date(ApproximateDate(future=True))
    {'start': None, 'end': None, 'formatted': ''}
    >>> date_to_popit_partial_date(None)
    {'start': None, 'end': None, 'formatted': ''}

    """

    if approx_date:
        year = approx_date.year
        month = approx_date.month
        day = approx_date.day
        if year and month and day:
            d = datetime.date(year, month, day)
            iso = date_to_iso_datetime(d)
            return {'start': iso,
                    'end': iso,
                    'formatted': d.strftime("%d %B %Y")}
        elif year and month and not day:
            start_d = datetime.date(year, month, 1)
            if month == 12:
                new_year = year + 1
                new_month = 1
            else:
                new_year = year
                new_month = month + 1
            end_d = datetime.date(new_year, new_month, 1)
            end_d -= datetime.timedelta(days=1)
            return {'start': date_to_iso_datetime(start_d),
                    'end': date_to_iso_datetime(end_d),
                    'formatted': str(month) + "/" + str(year)}
        elif year and not month and not day:
            start_d = datetime.date(year, 1, 1)
            end_d = datetime.date(year + 1, 1, 1)
            end_d -= datetime.timedelta(days=1)
            return {'start': date_to_iso_datetime(start_d),
                    'end': date_to_iso_datetime(end_d),
                    'formatted': str(year)}
        else:
            # print >> sys.stderr, "Unknown missing date values: year='%s', month='%s', day='%s' from approximate date: %s" % (year, month, day, approx_date)
            return {'start': None,
                    'end': None,
                    'formatted': ''}
    else:
        return {'start': None,
                'end': None,
                'formatted': ''}

def make_personal_details(dob, dod):
    return {'date_of_birth': date_to_popit_partial_date(dob),
            'date_of_death': date_to_popit_partial_date(dod)}

def create_organisations(popit):
    """Create organisations in PopIt based on those used in positions in Pombola

    Look through all positions in PopIt and find add the organisation
    that each refers to to PopIt.  Returns a dictionary where each key
    is a slug for an organisations in Pombola, and the value is the
    corresponding ID for the organisation in PopIt.
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
            new_organisation = popit.organisation.post({'slug': o.slug,
                                                        'name': o.name,
                                                        'category': oslug_to_category[o.slug]})
            slug_to_id[o.slug] = new_organisation['result']['_id']
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
        popit_options['api_version'] = 'v1'

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

            # Remove all the "person", "organisation" and "position"
            # objects from PopIt.  Currently there's no command to
            # delete all in one go, so we have to do it one-by-one.

            for p in popit.person.get()['results']:
                print >> sys.stderr, "deleting the person:", p
                popit.person(p['_id']).delete()

            for o in popit.organisation.get()['results']:
                print >> sys.stderr, "deleting the organisation:", o
                popit.organisation(o['_id']).delete()

            for p in popit.position.get()['results']:
                print >> sys.stderr, "deleting the position:", p
                popit.position(p['_id']).delete()

            # Create all the organisations found in Pombola, and get
            # back a dictionary mapping the Pombola organisation slug
            # to the PopIt ID.

            org_slug_to_id = create_organisations(popit)

            # Create a person in PopIt for each Person in Pombola:

            for person in Person.objects.all():
                name = person.legal_name
                print >> sys.stderr, "creating the person:", name
                new_person = popit.person.post({'name': name})
                person_id = new_person['result']['_id']
                properties = {"personal_details": make_personal_details(person.date_of_birth,
                                                                        person.date_of_death)}
                if person.primary_image():
                    properties['images' ] = [{'url': base_url + person.primary_image().url}]
                result = popit.person(person_id).put(properties)
                for position in person.position_set.all():
                    if not (position.title and position.title.name):
                        continue
                    properties = {'title': position.title.name,
                                  'person': person_id,
                                  'start_date': date_to_popit_partial_date(position.start_date),
                                  'end_date': date_to_popit_partial_date(position.end_date)}
                    if position.organisation:
                        oslug = position.organisation.slug
                        organisation_id = org_slug_to_id[oslug]
                        properties['organisation'] = organisation_id
                    print >> sys.stderr, "  creating the position:", position
                    new_position = popit.position.post(properties)

        except slumber.exceptions.HttpClientError, e:
            print "Exception is:", e
            print "Error response content is", e.content
            sys.exit(1)
