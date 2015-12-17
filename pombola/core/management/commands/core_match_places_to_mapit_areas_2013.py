import sys

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from pombola.core import models
from mapit import models as mapit_models


class Command(NoArgsCommand):
    help = 'Link places to areas in mapit for the new 2013 places'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):
        self.match_for_types(type_code='con',
                             mapit_generation=3,
                             place_kind_slug='constituency',
                             session_slug='na2013',
                             commit=options['commit'])
        self.match_for_types(type_code='dis',
                             mapit_generation=3,
                             place_kind_slug='county',
                             session_slug='s2013',
                             commit=options['commit'],
                             suffix=True)

    def match_for_types(self, type_code, mapit_generation, place_kind_slug, session_slug, commit, suffix=False):

        # Get these even if not used so that we know that they exist
        area_type  = mapit_models.Type.objects.get( code = type_code )
        generation = mapit_models.Generation.objects.get( pk = mapit_generation )
        place_kind = models.PlaceKind.objects.get( slug = place_kind_slug )
        session = models.ParliamentarySession.objects.get(slug = session_slug)

        # Find all relevant areas to match
        areas = mapit_models.Area.objects.filter(type=area_type,
                                                 generation_low__lte=generation,
                                                 generation_high__gte=generation)

        all_places = set(models.Place.objects.filter(kind=place_kind, parliamentary_session=session))

        for area in areas:

            # Use the slug for matching, easiest way to normalize
            slug = slugify( area.name )
            if suffix:
                slug += '-' + place_kind.slug
            else:
                slug += '-2013'

            # find it and update, or print out an error for a human to follow up
            try:
                place = models.Place.objects.get(slug=slug,
                                                 kind=place_kind,
                                                 parliamentary_session=session)
                place.mapit_area = area
                if commit:
                    print >> sys.stderr, "Saving", place
                    place.save()
                else:
                    print >> sys.stderr, "Not saving %s, since --commit wasn't specified" % (place,)

                all_places.discard(place)

            except models.Place.DoesNotExist:
                print "Could not find matching place for mapit area '%s' (%s, %s)" % ( area.name, slug, place_kind_slug )

        if all_places:
            for place in all_places:
                print "Could not find the place %s in MapIt (%s)" % (place, slugify(place.name))
