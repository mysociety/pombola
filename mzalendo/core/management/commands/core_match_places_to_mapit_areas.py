from optparse import make_option
from pprint import pprint

from django.core.management.base import NoArgsCommand
from django.template.defaultfilters import slugify
from django.conf import settings

# from helpers import geocode
from core import models
from mapit import models as mapit_models

class Command(NoArgsCommand):
    help = 'Link places to areas in mapit'

    def handle_noargs(self, **options):
        self.match_for_types(type_code='con', place_kind_slug='constituency')


    def match_for_types(self, type_code, place_kind_slug ):

        # Get these even if not used so that we know that they exist
        area_type  = mapit_models.Type.objects.get( code = type_code )
        place_kind = models.PlaceKind( slug = place_kind_slug )

        # Find all relevant areas to match
        areas = mapit_models.Area.objects.filter( type = area_type )

        for area in areas:

            # Use the slug fer matching, easiet way to normalize
            slug = slugify( area.name )
            
            # find it and update, or print out an error for a human to follow up
            try:
                place = models.Place.objects.get(slug=slug, kind__slug=place_kind_slug)
                place.mapit_area = area
                place.save()
            except models.Place.DoesNotExist:
                print "Could not find matching place for mapit area '%s' (%s, %s)" % ( area.name, slug, place_kind_slug )

