from optparse import make_option
from pprint import pprint

from django.core.management.base import NoArgsCommand
from django.template.defaultfilters import slugify
from django.conf import settings

from mzalendo.helpers import geocode
from mzalendo.core import models


class Command(NoArgsCommand):
    help = 'Fetch the areas from mapit'

    area_types_to_fetch = ('CTR','PRO','DIS','DIV')

    def handle_noargs(self, **options):

        data = geocode.get_mapit_url( 'areas', [','.join(self.area_types_to_fetch)] )

        for entry in data.values():
            # pprint( entry )
            
            # get the place kind
            kind, kind_created = models.PlaceKind.objects.get_or_create(
                name = entry['type_name'],
                defaults = {
                    'slug': slugify( entry['type_name'] ),
                }
            )
            
            # get or create the place
            print "updating/adding '%s'" % ( entry['name'] )
            place = models.Place.objects.update_or_create(
                {
                    'name': entry['name'],
                    'kind': kind,
                },
                {
                    'slug':     slugify( entry['name'] + ' ' + entry['type_name'] ),
                    'mapit_id': entry['id'],
                }
            )
    