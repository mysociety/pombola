# -*- encoding: utf-8 -*-

import csv
import os
import re
import sys
from optparse import make_option

from pombola.core.models import Organisation, Place
from pombola.south_africa.models import ZAPlace
from django.core.management.base import NoArgsCommand


data_directory = os.path.join(
    sys.path[0], 'pombola', 'south_africa', 'data', 'adwords')

class Command(NoArgsCommand):
    help = 'Generate CSV files with data for generating Google AdWords'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):
        # write out representatives csv
        headings = ['Name', 'MzURL', 'Parliament', 'Province', 'Parties', 'Positions', 'Keywords']
        self.write_adwords_csv(
            os.path.join(data_directory, 'representatives.csv'),
            headings,
            self.representatives_row_generator
        )

        # write out the provinces csv
        headings = ['Province', 'MzURL', 'Keywords']
        self.write_adwords_csv(
            os.path.join(data_directory, 'provinces.csv'),
            headings,
            self.provinces_row_generator
        )

        # write out the parties csv
        headings = ['Party', 'MzURL', 'Keywords']
        self.write_adwords_csv(
            os.path.join(data_directory, 'parties.csv'),
            headings,
            self.parties_row_generator
        )

        # write out the constituency offices csv
        headings = ['Constituency Office', 'MzURL', 'Keywords']
        self.write_adwords_csv(
            os.path.join(data_directory, 'constituency_offices.csv'),
            headings,
            self.constituency_offices_row_generator
        )


    def write_adwords_csv(self, filename, headings, row_generator):
        with open(filename, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=headings)
            writer.writerow(dict((h, h) for h in headings))

            for row in row_generator():
                writer.writerow({
                    k: unicode(v).encode('utf-8') for k, v in row.items()
                })


    def representatives_row_generator(self):
        for parliament in ('national-assembly', 'ncop'):
            for position in Organisation.objects.get(slug=parliament) \
                                .position_set.all() \
                                .currently_active() \
                                .order_by('person__id') \
                                .distinct('person__id'):

                person = position.person
                row = {'Name': person.legal_name,
                       'MzURL': 'http://www.pa.org.za' + person.get_absolute_url(),
                       'Parliament': position.organisation.name}
                place = position.place
                if place:
                    if place.kind.slug == 'province':
                        row['Province'] = place.name
                    else:
                        raise Exception, "Unknown place: %s" % (place)
                row['Parties'] = ", ".join(p.name.strip() for p in person.parties().filter(ended=''))
                person_positions = person.position_set.all() \
                                       .currently_active() \
                                       .exclude(organisation__kind__slug='party') \
                                       .exclude(organisation__kind__slug='parliament') \
                                       .exclude(title__slug="constituency-contact") \
                                       .exclude(title=None)

                if person_positions:
                    row['Positions'] = "; ".join(p.title.name.strip() + " at " + p.organisation.name.strip() for p in person_positions)

                yield(row)


    def provinces_row_generator(self):
        for place in Place.objects.filter(kind__slug = 'province'):

            yield({'Province': place.name,
                   'MzURL': 'http://www.pa.org.za' + place.get_absolute_url()})


    def parties_row_generator(self):
        for party in Organisation.objects.filter(kind__slug='party').filter(ended=''):

            yield({'Party': party.name,
                   'MzURL': 'http://www.pa.org.za' + party.get_absolute_url()})


    def constituency_offices_row_generator(self):
        CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS = (
            'constituency-office',
            'constituency-area', # specific to DA party
        )

        offices = ZAPlace.objects \
                    .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS) \
                    .order_by('organisation__id') \
                    .distinct('organisation__id')

        for office in offices:
            if not office.organisation.is_ongoing():
                offices = offices.exclude(id=office.id)

        office_name_re = re.compile('^(?P<party>[\w\s]+)\sConstituency Office\s*(?:\(\d+\))?:\s*(?P<name>.*)$')

        for office in offices:
            result = office_name_re.match(office.organisation.name)

            if result:
                office_name = result.group('name') + ' Constituency Office'
                office_party_name = result.group('party') + ' ' + office_name

                yield({
                    'Constituency Office': office_party_name,
                    'MzURL': 'http://www.pa.org.za' + office.organisation.get_absolute_url()
                })
