import warnings

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404
from django.db.models import Count
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import mapit
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

from popit.models import Person as PopitPerson
from speeches.models import Section, Speech, Speaker
from speeches.views import SectionView, SpeakerView

from pombola.core import models
from pombola.core.views import PlaceDetailView, PlaceDetailSub, OrganisationDetailView, PersonDetail
from pombola.info.views import InfoPageView

from pombola.south_africa.models import ZAPlace

# In the short term, until we have a list of constituency offices and
# addresses from DA, let's bundle these together.
CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS = (
    'constituency-office',
    'constituency-area', # specific to DA party
)

class LatLonDetailView(PlaceDetailView):
    template_name = 'south_africa/latlon_detail_view.html'

    # Using 25km as the default, as that's what's used on MyReps.
    constituency_office_search_radius = 25

    def get_object(self):
        # FIXME - handle bad args better.
        lat = float(self.kwargs['lat'])
        lon = float(self.kwargs['lon'])

        self.location = Point(lon, lat)

        areas = mapit.models.Area.objects.by_location(self.location)

        try:
            # FIXME - Handle getting more than one province.
            province = models.Place.objects.get(mapit_area__in=areas, kind__slug='province')
        except models.Place.DoesNotExist:
            raise Http404

        return province

    def get_context_data(self, **kwargs):
        context = super(LatLonDetailView, self).get_context_data(**kwargs)
        context['location'] = self.location

        context['office_search_radius'] = self.constituency_office_search_radius

        context['nearest_offices'] = nearest_offices = (
            ZAPlace.objects
            .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
            .distance(self.location)
            .filter(location__distance_lte=(self.location, D(km=self.constituency_office_search_radius)))
            .order_by('distance')
            )

        return context

class SAPlaceDetailSub(PlaceDetailSub):
    child_place_template = "south_africa/constituency_office_list_item.html"
    child_place_list_template = "south_africa/constituency_office_list.html"

    def get_context_data(self, **kwargs):
        context = super(SAPlaceDetailSub, self).get_context_data(**kwargs)

        context['child_place_template'] = self.child_place_template
        context['child_place_list_template'] = self.child_place_list_template
        context['subcontent_title'] = 'Constituency Offices'

        if self.object.kind.slug == 'province':
            context['child_places'] = (
                ZAPlace.objects
                .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
                .filter(location__coveredby=self.object.mapit_area.polygons.collect())
                )
            
        return context


class SAOrganisationDetailView(OrganisationDetailView):

    def get_context_data(self, **kwargs):
        context = super(SAOrganisationDetailView, self).get_context_data(**kwargs)

        # Get all the parties represented in this house.
        people_in_house = models.Person.objects.filter(position__organisation=self.object)
        parties = models.Organisation.objects.filter(
            kind__slug='party',
            position__person__in=people_in_house,
        ).annotate(person_count=Count('position__person'))
        total_people = sum(map(lambda x: x.person_count, parties))

        # Calculate the % of the house each party occupies.
        for party in parties:
            party.percentage = round((float(party.person_count) / total_people) * 100, 2)

        context['parties'] = parties
        context['total_people'] =  total_people

        return context

    def get_template_names(self):
        if self.object.kind.slug == 'house':
            return [ 'south_africa/organisation_house.html' ]
        else:
            return super(SAOrganisationDetailView, self).get_template_names()


class SAPersonDetail(PersonDetail):

    important_organisations = ('ncop', 'national-assembly', 'national-executive')

    def get_sayit_speaker(self):
        # see also templatetags/pombola_speech_tags.py

        pombola_person = self.object

        try:
            i = models.Identifier.objects.get(
                content_type = models.ContentType.objects.get_for_model(models.Person),
                object_id = pombola_person.id,
                scheme = 'org.mysociety.za'
            )
            speaker = Speaker.objects.get(person__popit_id = i.scheme + i.identifier)
            return speaker

        except ObjectDoesNotExist:
            return None

    def get_recent_speeches_for_section(self, section_title):
        pombola_person = self.object
        sayit_speaker = self.get_sayit_speaker()

        if not sayit_speaker:
            # Without a speaker we can't find any speeches
            return Speech.objects.none()

        try:
            # Add parent=None as the title is not unique, hopefully the top level will be.
            sayit_section = Section.objects.get(title=section_title, parent=None)
        except Section.DoesNotExist:
            # No match. Don't raise exception but do produce a warning and then return an empty queryset
            warnings.warn("Could not find top level sayit section '{0}'".format(section_title))
            return Speech.objects.none()

        speeches = (
            sayit_section.descendant_speeches()
                .filter(speaker=sayit_speaker)
                .order_by('-start_date', '-start_time'))

        return speeches


    def get_context_data(self, **kwargs):
        context = super(SAPersonDetail, self).get_context_data(**kwargs)
        context['twitter_contacts'] = self.object.contacts.filter(kind__slug='twitter')
        context['email_contacts'] = self.object.contacts.filter(kind__slug='email')
        context['phone_contacts'] = self.object.contacts.filter(kind__slug__in=('cell', 'voice'))
        context['fax_contacts'] = self.object.contacts.filter(kind__slug='fax')
        context['address_contacts'] = self.object.contacts.filter(kind__slug='address')
        context['positions'] = self.object.politician_positions().filter(organisation__slug__in=self.important_organisations)

        # FIXME - the titles used here will need to be checked and fixed.
        context['hansard']   = self.get_recent_speeches_for_section("Hansard")
        context['committee'] = self.get_recent_speeches_for_section("Committee Minutes")
        context['questions'] = self.get_recent_speeches_for_section("Questions")

        return context


search_models = (
    models.Place,
    models.PositionTitle,
)
if settings.ENABLED_FEATURES['speeches']:
    from speeches.models import Speech
    search_models += ( Speech, )


class SASearchView(SearchView):

    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = SearchQuerySet().models(*search_models).highlight()
        return super(SASearchView, self).__init__(*args, **kwargs)

    def extra_context(self):
        if not self.query:
            return {}
        query = SearchQuerySet().highlight()
        return {
            'person_results': query.models(models.Person).filter(content=AutoQuery(self.request.GET['q'])),
            'organisation_results': query.models(models.Organisation).filter(content=AutoQuery(self.request.GET['q'])),
        }


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'

class SASectionView(SectionView):
    def get_context_data(self, **kwargs):
        context = super(SASectionView, self).get_context_data(**kwargs)

        context['speechlist_name'] = 'hansard' # TODO parametrize this based on section parent
        return context

class SASpeakerView(SpeakerView):
    pass
