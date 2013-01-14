# This script imports the boundaries for the 2013 Kenyan election into
# MapIt - it uses the generic mapit_import script.

import json
import os
import sys
import urllib

from tempfile import NamedTemporaryFile

from optparse import make_option

from django.core.management import call_command
from django.core.management.base import NoArgsCommand

from mapit.models import Generation

class Command(NoArgsCommand):
    help = 'Import boundaries for the 2013 election'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):

        new = Generation.objects.new()
        if not new:
            raise Exception, "There's no new inactive generation to import into"

        geojson_urls = (('dis', 'COUNTY_NAM', 'http://vote.iebc.or.ke/js/counties.geojson'),
                        ('con', 'CONSTITUEN', 'http://vote.iebc.or.ke/js/constituencies.geojson'))

        for area_type_code, name_field, url in geojson_urls:
            f = urllib.urlopen(url)
            data = json.load(f)
            f.close()
            data['features'] = [f for f in data['features'] if f['properties']['COUNTY_NAM']]
            with NamedTemporaryFile(delete=False) as ntf:
                json.dump(data, ntf)
            print >> sys.stderr, ntf.name

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

            call_command('mapit_import', ntf.name, **keyword_arguments)

            os.remove(ntf.name)
