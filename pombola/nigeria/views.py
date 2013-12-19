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
                senatorial_district_areas = Area.objects.filter(type__code="SEN", polygons__polygon__intersects=area_polygons)
                context['senatorial_districts'] = self.convert_areas_to_places(senatorial_district_areas)

                federal_constituency_areas = Area.objects.filter(type__code="FED", polygons__polygon__intersects=area_polygons)
                context['federal_constutencies'] = self.convert_areas_to_places(federal_constituency_areas)

        return context


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
