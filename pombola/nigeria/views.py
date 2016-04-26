import re

from mapit.models import Area

from info.models import InfoPage

from pombola.core.models import Place
from pombola.core.views import HomeView
from pombola.search.views import SearchBaseView


class NGHomeView(HomeView):

    def get_context_data(self, **kwargs):
        context = super(NGHomeView, self).get_context_data(**kwargs)

        context['blog_posts'] = InfoPage.objects.filter(
            categories__slug="latest-news",
            kind=InfoPage.KIND_BLOG
        ).order_by("-publication_date")

        # If there is editable homepage content make it available to the templates.
        # Currently only Nigeria uses this, if more countries want it we should
        # probably add a feature flip boolean to the config.
        try:
            page = InfoPage.objects.get(slug="homepage")
            context['editable_content'] = page.content_as_html
        except InfoPage.DoesNotExist:
            context['editable_content'] = None
        return context

# These are hardcoded here rather than being introduced into the database to
# avoid having a huge number of duplicated codes in MapIt. As it is largely a
# presentation thing though I don't think it is too big an issue.
state_number_to_letter_mappings = {
    "1": "AB",
    "2": "AD",
    "3": "AK",
    "4": "AN",
    "5": "BA",
    "6": "BY",
    "7": "BE",
    "8": "BO",
    "9": "CR",
    "10": "DE",
    "11": "EB",
    "12": "ED",
    "13": "EK",
    "14": "EN",
    "15": "GO",
    "16": "IM",
    "17": "JI",
    "18": "KD",
    "19": "KN",
    "20": "KT",
    "21": "KE",
    "22": "KO",
    "23": "KW",
    "24": "LA",
    "25": "NA",
    "26": "NI",
    "27": "OG",
    "28": "ON",
    "29": "OS",
    "30": "OY",
    "31": "PL",
    "32": "RI",
    "33": "SO",
    "34": "TA",
    "35": "YO",
    "36": "ZA",
    "37": "FC",
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

# A regular expression to match any PUN after it's been tidied
pun_re = re.compile('''
    ^(
       [A-Z]{2}|
       [A-Z]{2}:\d+|
       [A-Z]{2}:\d+:\d+|
       [A-Z]{2}:\d+:\d+:\d+
    )$
''', re.VERBOSE)


class NGSearchView(SearchBaseView):

    def get_template_names(self):
        if self.pun:
            return ['search/poll-unit-number.html']
        else:
            return super(NGSearchView, self).get_template_names()

    def get_context_data(self, **kwargs):
        context = super(NGSearchView, self).get_context_data(**kwargs)

        if self.pun is None:
            return context

        # So now we know that the query is a PUN:
        query = tidy_up_pun(self.request.GET.get('q'))
        context['raw_query'] = query
        context['query'] = query
        context['area'] = self.get_area_from_pun(query)

        # If area found find places of interest
        if context['area']:
            area = context['area']

            # Get the area PUN and name to store in context for template
            context['area_pun_code'] = area.codes.filter(type__code="poll_unit")[0].code
            context['area_pun_name'] = area.names.filter(type__code="poll_unit")[0].name

            # Get the place object for the containing state
            context['state'] = self.get_state(
                context['area_pun_code'],
                query[0:2],
                area)

            # work out what level of the PUN we've matched
            context['area_pun_type'] = self.get_pun_type(context['area_pun_code'])

            # attempt to populate governor info
            context['governor'] = self.find_governor(context['state'])

            # work out the polygons to match to, may need to go up tree to parents.
            area_for_polygons = self.find_containing_area(area)
            if area_for_polygons:
                area_polygons = area_for_polygons.polygons.collect()

                context['federal_constituencies'] = self.get_district_data(
                    self.find_matching_places("FED", area_polygons),
                    "representative"
                )

                context['senatorial_districts']  = self.get_district_data(
                    self.find_matching_places("SEN", area_polygons),
                    "senator"
                )
        return context

    def parse_params(self):
        super(NGSearchView, self).parse_params()
        tidied_as_if_pun = tidy_up_pun(self.query)
        # Check if this is a known form of PUN:
        if pun_re.search(tidied_as_if_pun):
            self.pun = tidied_as_if_pun
        else:
            self.pun = None

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        return super(NGSearchView, self).get(request, *args, **kwargs)

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

    def get_area_from_pun(self, pun):
        """Find MapIt area that matches the PUN.

        If not found trim off components from the end until match
        or no more searches possible.
        Need this as we don't have the polling stations and want to be
        forgiving in case of input error.
        """

        while pun:
            try:
                area = Area.objects.get(codes__code=pun)
                return area
            except Area.DoesNotExist:
                # strip off last component
                pun = re.sub(r'[^:]+$', '', pun)
                pun = re.sub(r':$', '', pun)

    def get_state(self, matched_pun, state_code, area):
        if ":" in matched_pun:
            # look up state
            state_area = self.get_area_from_pun(state_code)
        else:
            # matched area is the state, convert it to place data
            state_area = area
        return self.convert_area_to_place(state_area)

    def find_governor(self, state):
        if state:
            governor = self.get_people(state, "executive-governor")
            if governor:
                return governor[0][0]

    def find_containing_area(self, area):
        area_for_polygons = area
        while area_for_polygons and not area_for_polygons.polygons.exists():
            area_for_polygons = area_for_polygons.parent_area
        return area_for_polygons

    def get_pun_type(self, pun):
        # use the length of the matched PUN to determine whether
        # we've matched a ward, an lga or a state
        # ref: http://www.inecnigeria.org/?page_id=20
        pun_level = pun.count(':')
        if pun_level == 2:
            return 'ward'
        elif pun_level == 1:
            return 'local government area'
        else:
            return 'state'

    def get_district_data(self, districts, role):
        district_list = []
        for district in districts:
            place = {}
            place['district_name'] = district.name
            place['district_url'] = district.get_absolute_url()
            people = self.get_people(district, role)
            if people:
                place['rep_name'] = people[0][0].name
                place['rep_url'] = people[0][0].get_absolute_url()
            district_list.append(place)
        return district_list

    def get_people(self, place, role):
        return place.related_people(
            lambda qs: qs.filter(person__position__title__slug=role))
