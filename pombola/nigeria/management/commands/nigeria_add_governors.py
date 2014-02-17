import csv
import datetime
import os
import re
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.template.defaultfilters import slugify
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import (
    Person, Place, Position, PositionTitle, Organisation)

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

def adjust_approximate_date(ad, by_days):
    """Return an ApproximateDate offset from another by some days

    This refuses to adjust a 'future' ApproximateDate, and treats
    those without month or day specified as being on the first day of
    the month, or the first day of the year respectively.

    >>> ad = ApproximateDate(2014, 2, 17)
    >>> adjust_approximate_date(ad, -1)
    2014-02-16
    >>> ad = ApproximateDate(2014, 1, 1)
    >>> adjust_approximate_date(ad, -1)
    2013-12-31
    >>> ad = ApproximateDate(2014, 2)
    >>> adjust_approximate_date(ad, 50)
    2014-03-23
    >>> ad = ApproximateDate(2014)
    >>> adjust_approximate_date(ad, 40)
    2014-02-10
    """

    if ad.future:
        raise Exception, "You can't adjust a future date"
    day = ad.day or 1
    month = ad.month or 1
    d = datetime.date(ad.year, month, day)
    d = d + datetime.timedelta(days=by_days)
    return ApproximateDate(d.year, d.month, d.day)

# FIXME: this is a variant of code from core_import_popolo.py; this
# repetition should be refactored out, either into commonlib or just
# within this repository:

def get_or_create(model, **kwargs):
    """An alternative to Django's get_or_create where save() is optional

    This is based on Django's get_or_create from
    django/db/models/query.py, but in this version the special keyword
    argument 'commit' (which defaults to True) can be set to False to
    specify that the model shouldn't be saved."""

    commit = kwargs.pop('commit', False)
    defaults = kwargs.pop('defaults', {})
    lookup = kwargs.copy()
    try:
        result = model.objects.get(**lookup)
        print "  Found {0} with params {1}".format(model.__name__, lookup)
        return result
    except model.DoesNotExist:
        params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
        params.update(defaults)
        o = model(**params)
        if commit:
            print "  Saving {0} with params {1}".format(model.__name__, kwargs)
            o.save()
        else:
            print "  Not saving {0} (no --commit) with params {1}".format(model.__name__, kwargs)
        return o
    raise Exception("Failed get_or_create")

class Command(NoArgsCommand):

    help = "Import the state governors of Nigeria, as of February 2014"

    option_list = NoArgsCommand.option_list + (
        make_option('--commit',
                    action='store_true',
                    default=False,
                    dest='commit',
                    help='Actually update the database'),
    )

    def handle_noargs(self, **options):

        command_directory = os.path.dirname(__file__)
        data_directory = os.path.realpath(
            os.path.join(command_directory,
                         '..',
                         '..',
                         'data'))

        governor_pt = get_or_create(
            PositionTitle,
            commit=options['commit'],
            name='Governor',
            slug='governor')

        party_member_pt = get_or_create(
            PositionTitle,
            commit=options['commit'],
            name='Member',
            slug='member')

        with open(os.path.join(data_directory,
                               'governors-wikipedia-2012-02-14.csv')) as f:

            reader = csv.DictReader(f)
            for row in reader:
                place_name = row['Place Name']
                place_name = re.sub('(?i)\s+State\s*$', '', place_name)

                place = Place.objects.get(kind__slug='state',
                                          name=place_name)

                person_name = row['Current Governor']
                person_slug = slugify(person_name)
                person = get_or_create(
                    Person,
                    commit=options['commit'],
                    slug=person_slug,
                    legal_name=person_name)

                office_start_date = parse_approximate_date(row['Elected/Took office'])

                governor_position = get_or_create(
                    Position,
                    commit=options['commit'],
                    person=person,
                    place=place,
                    title=governor_pt,
                    category='political',
                    defaults={
                        'organisation': None,
                        'start_date': office_start_date,
                        'end_date': ApproximateDate(future=True)
                     })

                # Now create party memberships:

                party_details = row['Party'].strip()

                party_position_a = None
                party_position_b = None

                if party_details:

                    m = re.search(r'^([^;]+)(?:; (.+) from ((\d{4})(?:-(\d{2})(?:-(\d{2}))?)?))?$',
                                  party_details)

                    if not m:
                        raise Exception, "Unknown format of party '{0}'".format(party_details)

                    party_a, party_b, b_onward_date, b_onward_year, b_onward_month, b_onward_day = m.groups()

                    # Create a position in that party:
                    party = Organisation.objects.get(kind__slug='party',
                                                     name=party_a)
                    end_date = ApproximateDate(future=True)

                    party_position_a = get_or_create(
                        Position,
                        commit=options['commit'],
                        person=person,
                        place=None,
                        title=party_member_pt,
                        category='political',
                        organisation=party,
                        defaults={
                            'start_date': office_start_date,
                            'end_date': ApproximateDate(future=True)
                         })

                    if party_b:
                        new_party_from = parse_approximate_date(b_onward_date)
                        old_part_to = adjust_approximate_date(
                            new_party_from, -1)

                        party_position_a.end_date = old_part_to
                        if options['commit']:
                            party_position_a.save()

                        party = Organisation.objects.get(kind__slug='party',
                                                         name=party_b)

                        party_position_b = get_or_create(
                            Position,
                            commit=options['commit'],
                            person=person,
                            place=None,
                            title=party_member_pt,
                            category='political',
                            organisation=party,
                            defaults={
                                'start_date': new_party_from,
                                'end_date': ApproximateDate(future=True)
                            })
