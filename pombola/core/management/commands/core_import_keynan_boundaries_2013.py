# This script imports the boundaries for the 2013 Kenyan election into
# MapIt - it uses the generic mapit_import script.

import string
import sys

from optparse import make_option

from django.core.management import call_command
from django.core.management.base import NoArgsCommand, CommandError

from mapit.models import Generation, Area


def map_county_name(original_name):
    # Then title-case the string, being careful to use string.capwords
    # instead of str.title, due to apostrophes in some names:
    result = string.capwords(original_name)
    fixes = {"Elgeyo - Marakwet": "Elgeyo-Marakwet",
             "Homabay": "Homa Bay",
             "Muranga": "Murang'a",
             "Trans Nzoia": "Trans-Nzoia",
             "Makuen": "Makueni",
             "Tharaka": "Tharaka-Nithi"}
    return fixes.get(result, result)

def map_constituency_name(original_name):
    # There are a few errors that Jessica spotted:
    fixes = {"DAADAB": "DADAAB",
             "WEBUTE WEST": "WEBUYE WEST"}
    return fixes.get(original_name, original_name)

class Command(NoArgsCommand):
    help = 'Import boundaries for the 2013 election'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--counties_shpfile', dest='counties_shpfile', help='The counties .shp file (required)'),
        make_option('--constituencies_shpfile', dest='constituencies_shpfile', help='The constituencies .shp file (required)'),
    )

    def handle_noargs(self, **options):

        new = Generation.objects.new()
        if not new:
            raise Exception, "There's no new inactive generation to import into"

        for required in ('constituencies_shpfile', 'counties_shpfile'):
            if not options[required]:
                raise CommandError("You must specify --" + required)

        all_data = (('dis', 'COUNTY_NAM', map_county_name, options['counties_shpfile']),
                    ('con', 'CONSTITUEN', map_constituency_name, options['constituencies_shpfile']))

        for area_type_code, name_field, map_name_function, filename in all_data:

            keyword_arguments = {'generation_id': new.id,
                                 'area_type_code': area_type_code,
                                 'name_type_code': 'name',
                                 'country_code': 'k',
                                 'name_field': name_field,
                                 'code_field': None,
                                 'code_type': None,
                                 'encoding': None,
                                 'preserve': True,
                                 'verbose': True,
                                 'use_code_as_id': None}
            keyword_arguments.update(options)

            call_command('mapit_import', filename, **keyword_arguments)

            # After a successful import, fix the names:
            for area in Area.objects.filter(type__code=area_type_code,
                                            generation_high__gte=new,
                                            generation_low__lte=new):
                mapped_name = map_name_function(area.name)
                if mapped_name != area.name:
                    print >> sys.stderr, "Changed %s to %s for %s" % (area.name, mapped_name, area)
                    area.name = mapped_name
                    if options['commit']:
                        print >> sys.stderr, "   ... saved change"
                        area.save()
                    else:
                        print >> sys.stderr, "   ... change not saved, since --commit wasn't specified"
