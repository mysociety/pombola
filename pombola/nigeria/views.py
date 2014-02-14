import re

from django.views.generic import ListView, TemplateView

from mapit.models import Area
from pombola.core.models import Place

# These are hardcoded here rather than being introduced into the database to
# avoid having a huge number of duplicated codes in MapIt. As it is largely a
# presentation thing though I don't think it is too big an issue.
state_number_to_letter_mappings = {
     "1":  "AB",
     "2":  "AD",
     "3":  "AK",
     "4":  "AN",
     "5":  "BA",
     "6":  "BN",
     "7":  "BO",
     "8":  "BY",
     "9":  "CR",
     "10": "DT",
     "11": "EB",
     "12": "ED",
     "13": "EK",
     "14": "EN",
     "15": "FC",
     "16": "GM",
     "17": "IM",
     "18": "JG",
     "19": "KB",
     "20": "KD",
     "21": "KG",
     "22": "KN",
     "23": "KT",
     "24": "KW",
     "25": "LA",
     "26": "NG",
     "27": "NW",
     "28": "OD",
     "29": "OG",
     "30": "OS",
     "31": "OY",
     "32": "PL",
     "33": "RV",
     "34": "SO",
     "35": "TR",
     "36": "YB",
     "37": "ZF",
}

def tidy_up_pun(pun):
    """
    Tidy up the query into something that looks like PUNs we are expecting

    # None returns empty string
    >>> tidy_up_pun(None)
    ''

    # Tidy up and strip as expected
    >>> tidy_up_pun("AB:01:23:45")
    'AB:1:23:45'
    >>> tidy_up_pun("AB--01::23 45")
    'AB:1:23:45'
    >>> tidy_up_pun("  AB--01::23 45  ")
    'AB:1:23:45'

    # Convert state numbers to state code, if found
    >>> tidy_up_pun("01:01:23:45")
    'AB:1:23:45'
    >>> tidy_up_pun("01")
    'AB'
    >>> tidy_up_pun("99:01:23:45")
    '99:1:23:45'
    """

    if not pun:
        pun = ""

    pun = pun.strip().upper()
    pun = re.sub(r'[^A-Z\d]+', ':', pun ) # separators to ':'
    pun = re.sub(r'^0+', '',  pun ) # trim leading zeros at start of string
    pun = re.sub(r':0+', ':', pun ) # trim leading zeros for each component

    # PUNs starting with a number shoud be converted to start with a state code
    if re.match(r'^\d', pun):
        state_number = pun.split(':')[0]
        state_code = state_number_to_letter_mappings.get(state_number, state_number)
        pun = re.sub(r'^' + state_number, state_code, pun)

    return pun

class SearchPollUnitNumberView(TemplateView):
    template_name = 'search/poll-unit-number.html'

    def get_context_data(self, **kwargs):
        context = super(SearchPollUnitNumberView, self).get_context_data(**kwargs)

        query = tidy_up_pun(self.request.GET.get('q'))
        context['raw_query'] = query

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
        """Find MapIt areas of 'code' type that overlap with 'polygons'

        Return every MapIt area of the specifiedE type such that at
        least 50% of polygons (a MultiPolygon) overlaps it; if there
        are no such areas, just return the 5 MapIt areas of the right
        type with the largest overlap
        """

        all_areas = Area.objects.filter(type__code=code, polygons__polygon__intersects=polygons).distinct()

        area_of_original = polygons.area

        size_of_overlap = {}

        # calculate the overlap
        for area in all_areas:
            area_polygons = area.polygons.collect()
            intersection = polygons.intersection(area_polygons)

            size_of_overlap[area] = intersection.area / area_of_original

        # Sort the results by the overlap size; largest overlap first
        all_areas = sorted(all_areas,
                           reverse=True,
                           key=lambda a: size_of_overlap[a])

        # get the most overlapping ones
        likely_areas = [a for a in all_areas if size_of_overlap[a] > 0.5]

        # If there are none display first five (better than nothing...)
        if not likely_areas:
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
