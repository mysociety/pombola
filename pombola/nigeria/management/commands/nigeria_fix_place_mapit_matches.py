import csv
import os
import sys
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError

from pombola.core.models import Place, PlaceKind, ParliamentarySession
from mapit.models import Area, Generation

class Command(NoArgsCommand):

    help = "Apply some manually found matches between MapIt Area and Place objects"

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):

        mapit_generation = Generation.objects.current()

        command_directory = os.path.dirname(__file__)
        data_directory = os.path.realpath(
            os.path.join(command_directory,
                         '..',
                         '..',
                         'data'))

        required_columns = (
            'MapItCodeType',
            'MapItAreaName',
            'PombolaPlaceKindName',
            'PombolaPlaceName')

        with open(os.path.join(data_directory,
                         'manually-matched-FED-and-SEN.csv')) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not all(row[k] for k in required_columns):
                    continue

                placekind = PlaceKind.objects.get(
                    name=row['PombolaPlaceKindName'])
                place = Place.objects.get(
                    kind=placekind,
                    name=row['PombolaPlaceName'])

                print "got place:", place

                mapit_area = Area.objects.get(
                    type__code=row['MapItCodeType'],
                    generation_low__lte=mapit_generation,
                    generation_high__gte=mapit_generation,
                    name=row['MapItAreaName'])

                if place.mapit_area == mapit_area:
                    print "  MapIt area already correct:", mapit_area
                elif not place.mapit_area:
                    print "  MapIt area unset, setting to:", mapit_area
                    place.mapit_area = mapit_area
                    if options['commit']:
                        print "  Saving"
                        place.save()
                    else:
                        print "  Not saving, since --commit not specified"
                else:
                    message = "There was an unexpected MapIt area already present ({0}: {1});"
                    message += " would have tried to set it to {2} {3}"
                    raise Exception, message.format(place.mapit_area.id,
                                                    place.mapit_area,
                                                    mapit_area.id,
                                                    mapit_area)
