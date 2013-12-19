import re

from django.views.generic import ListView, TemplateView

from mapit.models import Area
from pombola.core.models import Place

class SearchPollUnitNumberView(TemplateView):
    template_name = 'search/poll-unit-number.html'

    def get_context_data(self, **kwargs):
        context = super(SearchPollUnitNumberView, self).get_context_data(**kwargs)

        query = self.request.GET.get('q')
        context['raw_query'] = query

        # tidy up the query into something that looks like PUNs we are expecting
        if query:
            query = query.upper()
            query = re.sub(r'[^A-Z\d]+', ':', query ) # separators to ':'
            query = re.sub(r':0+', ':', query ) # trim leading zeros

        context['query'] = query
        context['area'] = None
        context['results'] = []

        # Find mapit area that matches the PUN. If not found trim off
        # components from the end until match or no more searches possible.
        # Need this as we don't have the polling stations and want to be
        # forgiving in case of input error.
        while query:
            try:
                context['area'] = Area.objects.get(codes__code=query)
                break
            except Area.DoesNotExist:
                # strip off last component
                query = re.sub(r'[^:]+$', '', query)
                query = re.sub(r':$', '', query)

        # If area found find places of interest
        if context['area']:
            area = context['area']

            # Get the area PUN and name to store in context for template
            context['area_pun_code'] = area.codes.filter(type__code="poll_unit")[0].code
            context['area_pun_name'] = area.names.filter(type__code="poll_unit")[0].name

            # work out the polygons to match to, may need to go up tree to parents.
            area_for_polygons = area
            while area_for_polygons and not area_for_polygons.polygons.exists():
                area_for_polygons = area_for_polygons.parent_area

            if area_for_polygons:
                area_polygons = area_for_polygons.polygons.collect()

                # get the overlapping senatorial districts
                context['senatorial_districts']  = self.find_matching_places("SEN", area_polygons)
                context['federal_constutencies'] = self.find_matching_places("FED", area_polygons)

        return context


    def find_matching_places(self, code, polygons):

        all_areas = Area.objects.filter(type__code=code, polygons__polygon__intersects=polygons).distinct()

        size_of_overlap = {}

        # calculate the overlap
        for area in all_areas:
            area_polygons = area.polygons.collect()
            intersection = polygons.intersection(area_polygons)

            # choose the smallest area
            smallest_area = min(polygons.area, area_polygons.area)

            intersection_fraction_of_smallest_area = intersection.area / smallest_area
            size_of_overlap[area] = intersection_fraction_of_smallest_area

        # Sort the results by the overlap size
        all_areas = sorted(
            all_areas,
            cmp=lambda x,y: cmp(size_of_overlap[x], size_of_overlap[y])
        )

        # get the most overlapping ones
        likely_areas = filter(
            lambda x: size_of_overlap[x] > 0.5,
            all_areas
        )

        # If there are none display first five (better than nothing...)
        if not len(likely_areas):
            likely_areas = all_areas[:5]

        return self.convert_areas_to_places(likely_areas)

    def convert_areas_to_places(self, areas):
        places = []
        for area in areas:
            place = self.convert_area_to_place(area)
            if place:
                places.append(place)

        return places

    def convert_area_to_place(self, area):
        try:
            return Place.objects.get(mapit_area=area)
        except Place.DoesNotExist:
            return None
