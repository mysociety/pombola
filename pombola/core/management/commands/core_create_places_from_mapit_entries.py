# This script will copy areas from mapit to core.places, including creating the
# place kind if required.


# import re
# import sys
from django.core.management.base import LabelCommand

from mapit.models import Type
from pombola.core.models import Place, PlaceKind
from django.template.defaultfilters import slugify

class Command(LabelCommand):
    help = 'Copy mapit.areas to core.places'
    args = '<mapit.type.code>'

    def handle_label(self,  mapit_type_code, **options):

        # load the mapit type
        mapit_type = Type.objects.get(code=mapit_type_code)

        # if needed create the core placetype
        placekind, created = PlaceKind.objects.get_or_create(
            name=mapit_type.description,
            defaults={
                'slug': slugify(mapit_type.description)
            }
        )

        # create all the places as needed for all mapit areas of that type
        for area in mapit_type.areas.all():
            print area.name
            place, created = Place.objects.get_or_create(
                name=area.name,
                kind=placekind,
                defaults={
                    'slug': slugify(area.name),
                }
            )
            
            place.mapit_area = area
            place.save()
            