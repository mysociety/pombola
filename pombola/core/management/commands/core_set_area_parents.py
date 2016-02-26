# This script tries to find a parent for each area in Pombola's
# core_place table by comparing polygons in MapIt.  You invoke the
# script by giving as command-line arguments a series of pairs of
# slugs from the core_placekind table, the first being the kind of the
# child place, and the second being the kind of the parent place.  For
# example, for Pombola Nigeria, you could run:
#
#   ./manage.py core_set_area_parents senatorial-district:state constituency:state
#
# This is quite a fuzzy assignment, since there are errors in the
# boundaries that we have for Nigeria, and not every Federal
# Constituency overlaps with only a single state anyway.  For example,
# the Federal Constituency "Awka North & South" is (according to our
# boundary data) split between the states "Anambra" and "Delta".
#
# This script is an interim measure so that there is in most cases a
# useful value in the parent_place_id column of core_place, and
# currently the code expects that to be present to produce data for
# the "Related Places" tab on Places pages.

import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mapit.models import Area
from pombola.core.models import Place, PlaceKind


PROPORTION_OVERLAP_REQUIRED = 0.98

# From: http://stackoverflow.com/q/3844801/223092
def check_all_equal(iterable):
    try:
        iterator = iter(iterable)
        first = next(iterator)
        return all(first == rest for rest in iterator)
    except StopIteration:
        return True

def get_mapit_type_for_pombola_placekind(placekind):
    types_in_mapit = set(x.mapit_area.type for x in
                         Place.objects.filter(kind=placekind).select_related('mapit_area')
                         if x.mapit_area)
    if len(types_in_mapit) == 0:
        raise Exception, "Couldn't find a MapIt type that corresponded to the PlaceKind %s" % (placekind,)
    elif len(types_in_mapit) == 1:
        return list(types_in_mapit)[0]
    else:
        raise Exception, "There were multiple MapIt types (%s) corresponding to the PlaceKind %s" % (", ".join(types_in_mapit), placekind)

@transaction.atomic
def recalculate_parents(child_placekind, child_type, parent_placekind, parent_type):

    # Set the parent_place_id column to NULL for every Place with the
    # child's PlaceKind, since we're going to recalculate them:
    Place.objects.filter(kind=child_placekind).update(parent_place=None)

    for place in Place.objects.filter(kind=child_placekind).all():
        child_area = place.mapit_area
        if not child_area:
            print "No MapIt area corresponded to", place, "- skipping"
            continue
        print "Looking for parents of", child_area
        child_multipolygon = child_area.polygons.collect()
        if not child_multipolygon.valid:
            print "The child area's multipolygon was invalid; simplifying it"
            child_multipolygon = child_multipolygon.simplify(tolerance=0)
        parent_areas = set([])
        for potential_parent_area in Area.objects.filter(type=parent_type,
                                                         polygons__polygon__intersects=child_multipolygon).distinct():
            collected_parent_polygon = potential_parent_area.polygons.collect()
            if not collected_parent_polygon.valid:
                print "The potential parent area's multipolygon was invalid; simplifying it"
                collected_parent_polygon = collected_parent_polygon.simplify(tolerance=0)
            intersection = child_multipolygon.intersection(collected_parent_polygon)
            proportion_overlap = intersection.area / child_multipolygon.area
            print "    proportion overlap was %0.2f with %s" % (proportion_overlap, potential_parent_area)
            if proportion_overlap > PROPORTION_OVERLAP_REQUIRED:
                parent_areas.add(potential_parent_area)
        if len(parent_areas) == 0:
            print "  Warning: no plausible parent area found for:", child_area
        elif len(parent_areas) > 1:
            print "  Warning: multiple parent areas found for:", child_area
        else:
            parent_area = list(parent_areas)[0]
            print "  Exactly one parent found, setting the parent:", parent_area
            print "  filter(mapit_area=%s, kind=%s)" % (parent_area.id, parent_placekind.id)
            parent_places = Place.objects.filter(mapit_area=parent_area, kind=parent_placekind)
            if parent_places.count() > 1:
                print "------ found multiple matching places -------"
                for pp in parent_places:
                    print pp
                print "---------------------------------------------"
                raise Exception("multiple places found")

            if len(parent_places):
                place.parent_place = parent_places[0]
            else:
                print parent_places
                raise Exception("no parent place found")
                place.parent_place = None

            place.save()

class Command(BaseCommand):
    args = 'placekind-slug1:placekind-slug2 placekind-slug3:placekind-slug ...'
    help = 'Guess a reasonable parent_place_id for places in core_place'

    def handle(self, *args, **options):

        child_parent_placekinds = []
        for arg in args:
            m = re.search('([-\w]+):([-\w]+)', arg)
            if not m:
                raise CommandError, "The argument '%s' was malformed" % (arg,)
            child_parent_placekinds.append(tuple(m.groups()))

        child_slugs = [x[0] for x in child_parent_placekinds]
        if len(child_slugs) != len(set(child_slugs)):
            raise CommandError, "You can only specify each child placekind once, since each child can only have one parent"

        for child_slug, parent_slug in child_parent_placekinds:

            child_placekind = PlaceKind.objects.get(slug=child_slug)
            parent_placekind = PlaceKind.objects.get(slug=parent_slug)

            child_type = get_mapit_type_for_pombola_placekind(child_placekind)
            parent_type = get_mapit_type_for_pombola_placekind(parent_placekind)

            recalculate_parents(child_placekind,
                                child_type,
                                parent_placekind,
                                parent_type)
