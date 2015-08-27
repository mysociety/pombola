import csv
import os
import sys
from optparse import make_option

from pombola.core.models import PopoloMembership
from django.core.management.base import NoArgsCommand


data_directory = os.path.join(sys.path[0], 'kenya', '2013-election-data')

class Command(NoArgsCommand):
    help = 'Generate a CSV file with all candiates for generating Google AdWords'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        headings = ['FullName', 'MzURL', 'AspirantPosition', 'County', 'Constituency', 'Ward', 'Parties', 'Keywords']

        with open('aspirants-county-and-smaller.csv', 'w') as fp:

            writer = csv.DictWriter(fp, fieldnames=headings)

            writer.writerow(dict((h, h) for h in headings))

            for race_type in ('governor',
                              'senator',
                              'women-representative',
                              'mp',
                              'ward-representative'):
                for position in Position.objects.filter(title__slug=('aspirant-' + race_type)).currently_active():
                    person = position.person
                    full_names = [person.legal_name]
                    full_names += [an.alternative_name for an in person.alternative_names.all()]
                    for full_name in set(full_names):
                        row = {'FullName': full_name,
                               'MzURL': 'http://info.mzalendo.com' + person.get_absolute_url(),
                               'AspirantPosition': race_type}
                        place = position.place
                        if place.kind.slug == 'ward':
                            row['Ward'] = place.name
                            row['Constituency'] = place.parent_place.name
                            row['County'] = place.parent_place.parent_place.name
                        elif place.kind.slug == 'constituency':
                            row['Constituency'] = place.name
                            row['County'] = place.parent_place.name
                        elif place.kind.slug == 'county':
                            row['County'] = place.name
                        else:
                            raise Exception, "Unknown place: %s" % (place)
                        row['Parties'] = ", ".join(p.name.strip() for p in person.parties())

                        for key, value in row.items():
                            row[key] = unicode(value).encode('utf-8')

                        writer.writerow(row)
